"""Offline tests: no model, no server. Run from the repo root: pytest harness/tests -v"""

import csv

from frugalai_harness.base import GenResult
from frugalai_harness.bench import FIELDS, summarise, write_csv, run_benchmark
from frugalai_harness.lmstudio import LMStudioBackend
from frugalai_harness.metrics import PeakRam, host_info
from frugalai_harness.ollama import OllamaBackend


class TestOllamaParsing:
    def test_server_timings_used_when_present(self):
        data = {
            "response": "hello",
            "eval_count": 50,
            "eval_duration": 5_000_000_000,       # 5 s
            "prompt_eval_count": 12,
            "prompt_eval_duration": 1_000_000_000,
            "load_duration": 500_000_000,
        }
        res = OllamaBackend.parse_response(data, wall_s=8.0)
        assert res.timing_source == "server"
        assert res.decode_tokens_per_s == 10.0          # 50 tokens / 5 s, not / 8 s
        assert res.ttft_s == 1.5
        assert res.prompt_tokens == 12

    def test_falls_back_to_wall_clock(self):
        res = OllamaBackend.parse_response({"response": "x", "eval_count": 20}, wall_s=4.0)
        assert res.timing_source == "wall"
        assert res.decode_tokens_per_s == 5.0
        assert res.ttft_s is None

    def test_zero_tokens_gives_no_rate(self):
        res = OllamaBackend.parse_response({}, wall_s=1.0)
        assert res.decode_tokens_per_s is None


class _Clock:
    """Deterministic clock for stream parsing: each call advances by `step`."""

    def __init__(self, start=0.0, step=1.0):
        self.t = start
        self.step = step

    def __call__(self):
        self.t += self.step
        return self.t


class TestLMStudioParsing:
    def _lines(self, with_usage=True):
        out = [
            'data: {"choices":[{"delta":{"role":"assistant"}}]}',
            'data: {"choices":[{"delta":{"content":"Hel"}}]}',
            'data: {"choices":[{"delta":{"content":"lo"}}]}',
            'data: {"choices":[{"delta":{"content":"!"}}]}',
        ]
        if with_usage:
            out.append('data: {"choices":[],"usage":{"prompt_tokens":9,"completion_tokens":3}}')
        out.append("data: [DONE]")
        return out

    def test_text_and_usage(self):
        res = LMStudioBackend.parse_stream(self._lines(), t0=0.0, clock=_Clock())
        assert res.text == "Hello!"
        assert res.completion_tokens == 3
        assert res.prompt_tokens == 9
        assert res.timing_source == "stream"

    def test_decode_rate_excludes_time_to_first_token(self):
        # clock ticks: first content chunk -> 1.0, final read -> 2.0, so decode window is 1.0 s
        res = LMStudioBackend.parse_stream(self._lines(), t0=0.0, clock=_Clock())
        assert res.ttft_s == 1.0
        assert res.decode_tokens_per_s == 2.0            # (3 - 1) tokens / 1.0 s

    def test_counts_chunks_without_usage(self):
        res = LMStudioBackend.parse_stream(self._lines(with_usage=False), t0=0.0, clock=_Clock())
        assert res.completion_tokens == 3

    def test_reasoning_chunks_count_but_are_not_in_text(self):
        lines = [
            'data: {"choices":[{"delta":{"reasoning_content":"thinking"}}]}',
            'data: {"choices":[{"delta":{"content":"ok"}}]}',
            "data: [DONE]",
        ]
        res = LMStudioBackend.parse_stream(lines, t0=0.0, clock=_Clock())
        assert res.text == "ok"
        assert res.completion_tokens == 2
        assert res.reasoning_chunks == 1

    def test_no_reasoning_reports_zero(self):
        res = LMStudioBackend.parse_stream(self._lines(), t0=0.0, clock=_Clock())
        assert res.reasoning_chunks == 0

    def test_ollama_cannot_tell_so_reports_none(self):
        res = OllamaBackend.parse_response({"response": "x", "eval_count": 3}, wall_s=1.0)
        assert res.reasoning_chunks is None

    def test_garbage_lines_are_skipped(self):
        lines = [": keep-alive", "data: not-json", 'data: {"choices":[{"delta":{"content":"a"}}]}']
        res = LMStudioBackend.parse_stream(lines, t0=0.0, clock=_Clock())
        assert res.text == "a"


class TestEmbeddings:
    def test_lmstudio_reply_is_returned_in_input_order(self):
        data = {"data": [{"index": 1, "embedding": [0.0, 1.0]}, {"index": 0, "embedding": [1.0, 0.0]}]}
        assert LMStudioBackend.parse_embeddings(data) == [[1.0, 0.0], [0.0, 1.0]]

    def test_empty_reply_gives_empty_list(self):
        assert LMStudioBackend.parse_embeddings({}) == []


class TestAvailability:
    def test_unreachable_servers_report_false(self):
        # Port 1 never has a server: deterministic offline check.
        assert OllamaBackend("http://localhost:1").is_available() is False
        assert LMStudioBackend("http://localhost:1/v1").is_available() is False


class _FakeBackend:
    name = "fake"

    def __init__(self):
        self.calls = 0

    def generate(self, model, prompt, system="", max_tokens=256, temperature=0.2):
        self.calls += 1
        return GenResult("t", 10, 5, 1.0, 0.1, 20.0 + self.calls, "stream")


class TestBenchmark:
    def test_warmup_is_discarded_and_rows_counted(self):
        backend = _FakeBackend()
        rows = run_benchmark(backend, "m", "dev", prompts=["a", "b"], repeats=2, log=lambda s: None)
        assert len(rows) == 4                             # 2 prompts x 2 repeats
        assert backend.calls == 5                         # plus one discarded warm-up
        assert all(r["device"] == "dev" for r in rows)

    def test_summary_uses_median(self):
        rows = [{"decode_tokens_per_s": v, "peak_runtime_ram_mb": 100 + v} for v in (10.0, 30.0, 20.0)]
        s = summarise(rows)
        assert s["median_decode_tokens_per_s"] == 20.0
        assert s["peak_runtime_ram_mb"] == 130

    def test_summary_handles_missing_values(self):
        s = summarise([{"decode_tokens_per_s": None, "peak_runtime_ram_mb": None}])
        assert s["median_decode_tokens_per_s"] is None

    def test_csv_round_trip(self, tmp_path):
        rows = run_benchmark(_FakeBackend(), "m", "dev", prompts=["a"], repeats=1, log=lambda s: None)
        out = write_csv(rows, tmp_path / "sub" / "r.csv")
        with open(out, newline="", encoding="utf-8") as fh:
            read = list(csv.DictReader(fh))
        assert list(read[0].keys()) == FIELDS
        assert read[0]["model"] == "m"


class TestMetrics:
    def test_host_info_has_core_fields(self):
        info = host_info()
        assert info["ram_total_mb"] > 0
        assert info["cores_logical"] >= 1

    def test_peak_ram_none_when_no_process_matches(self):
        with PeakRam(hints=("zz-no-such-process-zz",), interval_s=0.05) as ram:
            pass
        assert ram.peak_mb is None
