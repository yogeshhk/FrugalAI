import datetime as dt
import shutil
import socket
import sqlite3

import numpy as np
import pytest

from voiceform import audio, config, netguard, pipeline, sinks
from voiceform.asr import FakeASR
from voiceform.evaluate import cer, eval_extract, score_record, summarise, wer
from voiceform.llm import FakeLLM
from voiceform.schema import load_forms

TODAY = dt.date(2026, 10, 31)
FORMS = load_forms()
TICKET = FORMS["service_ticket"]
SAID = "नाव हरी गावडे. गाव मोरगाव. मोबाईल नऊ चार शून्य चार शून्य चार शून्य चार एक एक. मोटर खूप आवाज करते. लगेच या."


def _ticket_reply():
    vals = {"customer_name": ("हरी गावडे", "हरी गावडे"), "village": ("मोरगाव", "गाव मोरगाव"),
            "phone": ("9404040411", "9 4 0 4 0 4 0 4 1 1"), "product": ("water_pump", "मोटर"),
            "problem": ("मोटर खूप आवाज करते", "मोटर खूप आवाज करते"), "urgency": ("high", "लगेच")}
    return {n: {"value": vals.get(n, (None, None))[0], "evidence": vals.get(n, (None, None))[1]} for n in TICKET.names}


def test_guard_blocks_the_internet_and_allows_this_machine():
    with netguard.offline() as g:
        with pytest.raises(netguard.Blocked):
            socket.create_connection(("93.184.216.34", 80), timeout=1)
        s = socket.socket()
        s.settimeout(0.2)
        try:
            s.connect(("127.0.0.1", 9))  # nothing listens there; the guard must let it try
        except OSError:
            pass
        finally:
            s.close()
    assert g.blocked == [("93.184.216.34", 80)] and g.local == 1
    socket.socket.connect  # restored after the block: a later test can still use the network


def test_guard_also_blocks_name_lookups_and_udp_and_can_be_nested():
    real = (socket.socket.connect, socket.socket.connect_ex, socket.socket.sendto, socket.getaddrinfo)
    with netguard.offline() as outer:
        with netguard.offline() as inner:
            with pytest.raises(socket.gaierror):
                socket.getaddrinfo("example.org", 80)
            udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            with pytest.raises(netguard.Blocked):
                udp.sendto(b"x", ("93.184.216.34", 53))
            udp.close()
            assert socket.getaddrinfo("localhost", 80)
        # the inner block ended; the outer guard must still be active, and both counted the attempts
        with pytest.raises(socket.gaierror):
            socket.getaddrinfo("example.com", 80)
        assert ("example.org", None) in inner.blocked and ("example.org", None) in outer.blocked
        assert ("example.com", None) in outer.blocked and ("example.com", None) not in inner.blocked
    assert (socket.socket.connect, socket.socket.connect_ex, socket.socket.sendto, socket.getaddrinfo) == real


def test_audio_load_refuses_anything_but_a_local_file():
    with pytest.raises(ValueError, match="not a local file"):
        audio.load("http://example.org/a.wav")
    with pytest.raises(ValueError, match="not a local file"):
        audio.load("tcp://93.184.216.34:80")


def test_pipeline_from_audio_is_offline_and_unconfirmed():
    turn = pipeline.run(TICKET, "mr", wav=np.zeros(16000, dtype=np.float32), asr=FakeASR([SAID]),
                        llm=FakeLLM([_ticket_reply()]), today=TODAY)
    assert turn.blocked_connections == 0
    assert turn.record.fields["phone"].value == "9404040411"
    assert turn.record.fields["product"].value == "water_pump"
    assert not turn.record.confirmed
    assert turn.timings["audio_seconds"] == 1.0
    assert "Create one 'Field service ticket' record" in turn.english


def test_sinks_refuse_unconfirmed_and_write_locally(tmp_path):
    turn = pipeline.run(TICKET, "mr", text=SAID, llm=FakeLLM([_ticket_reply()]), today=TODAY)
    with pytest.raises(sinks.NotConfirmed):
        sinks.send(turn.record, TICKET, outbox=tmp_path)
    turn.record.confirmed = True
    out = sinks.send(turn.record, TICKET, outbox=tmp_path)
    assert set(out) == set(sinks.SINKS) and all(p.exists() for p in out.values())
    with sqlite3.connect(out["sqlite"]) as con:
        row = con.execute('SELECT customer_name, phone FROM "service_ticket"').fetchone()
    assert row == ("हरी गावडे", "9404040411")
    assert "Nothing was sent" in out["api"].read_text(encoding="utf-8")


def test_wer_and_cer():
    assert wer("वय चोवीस वर्षे", "वय 24 वर्षे") == 0.0          # same after normalising
    assert wer("एक दोन तीन", "एक दोन") == pytest.approx(1 / 3, abs=0.01)
    assert cer("abc", "abd") == pytest.approx(1 / 3, abs=0.01)


def test_score_and_summary():
    turn = pipeline.run(TICKET, "mr", text=SAID, llm=FakeLLM([_ticket_reply()]), today=TODAY)
    gold = {"customer_name": "हरी गावडे", "village": "मोरगाव", "phone": "9404040411", "product": "water_pump",
            "problem": "मोटर खूप आवाज करते", "urgency": "high", "under_warranty": True}
    sc = score_record(TICKET, gold, turn.record)
    assert sc["correct"] == 6 and sc["missed"] == 1 and sc["to_fix"] == 1
    s = summarise([{**sc, "set": "tune", "seconds": 1.0}])
    assert s["tune"]["field_accuracy"] == round(6 / 7, 3)


def test_rules_evaluation_runs_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "RESULTS_DIR", tmp_path)
    out = eval_extract("mr", "rules", limit=4, verbose=False)
    assert out["summary"]["all"]["utterances"] == 4
    assert (tmp_path / f"{out['run']}.csv").exists()


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_audio_round_trip(tmp_path):
    tone = (0.3 * np.sin(2 * np.pi * 440 * np.arange(8000) / 16000)).astype(np.float32)
    back = audio.load(audio.save_wav(tmp_path / "t.wav", tone))
    assert len(back) == 8000 and np.max(np.abs(back - tone)) < 1e-3
    noisy = audio.add_noise(tone, 10)
    assert noisy.shape == tone.shape and not np.allclose(noisy, tone)


def test_downloads_are_pinned_and_do_not_fetch_python_by_default():
    from voiceform import download

    assert "*.py" not in download.HF_PATTERNS
    for name, spec in config.ASR_MODELS.items():
        if "repo" in spec:
            assert len(spec.get("revision", "")) == 40, f"{name} has no pinned 40-character revision"
    assert set(config.TTS_REVISIONS) == set(config.TTS_MODELS)
    assert all(len(v) == 40 for v in config.TTS_REVISIONS.values())
    for bad in ("", "TO_PIN"):
        with pytest.raises(ValueError):
            download.fetch_hf("some/repo", "x", bad)


def _fake_zip(files):
    import io
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return buf.getvalue()


def test_vosk_download_checks_hash_and_size(tmp_path, monkeypatch):
    import hashlib

    import requests

    from voiceform import download

    blob = _fake_zip({"m/a.txt": b"hello"})

    class Resp:
        content = blob

        def raise_for_status(self):
            pass

    monkeypatch.setattr(requests, "get", lambda url, timeout=0: Resp())
    good = hashlib.sha256(blob).hexdigest()
    download.fetch_vosk("http://x/m.zip", tmp_path / "ok", good)
    assert (tmp_path / "ok" / "m" / "a.txt").read_bytes() == b"hello"
    with pytest.raises(ValueError, match="checksum mismatch"):
        download.fetch_vosk("http://x/m.zip", tmp_path / "bad", "0" * 64)
    with pytest.raises(ValueError, match="no pinned SHA-256"):
        download.fetch_vosk("http://x/m.zip", tmp_path / "unpinned", "TO_PIN")
    assert not (tmp_path / "bad" / "m").exists() and not (tmp_path / "unpinned" / "m").exists()
    monkeypatch.setattr(download, "MAX_ZIP_BYTES", 3)
    with pytest.raises(ValueError, match="unpacks to more than"):
        download.fetch_vosk("http://x/m.zip", tmp_path / "big", good)


def test_downloaded_code_runs_only_if_its_hash_matches(tmp_path, monkeypatch):
    import hashlib

    good = b"print('reviewed')\n"
    (tmp_path / "model_onnx.py").write_bytes(good)
    monkeypatch.setattr(config, "CODE_SHA256", {"m": {"model_onnx.py": hashlib.sha256(good).hexdigest()}})
    config.verify_code_hash("m", str(tmp_path), "model_onnx.py")  # matches: no error
    (tmp_path / "model_onnx.py").write_bytes(b"print('changed upstream')\n")
    with pytest.raises(RuntimeError, match="refusing to run"):
        config.verify_code_hash("m", str(tmp_path), "model_onnx.py")
    with pytest.raises(RuntimeError, match="no reviewed SHA-256"):
        config.verify_code_hash("unknown", str(tmp_path), "model_onnx.py")
