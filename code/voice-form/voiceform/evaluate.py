"""Evaluation: speech step (WER, CER, real-time factor, RAM) and extraction step (field accuracy, fields to fix).

Conditions, kept apart so an error can be blamed on the right step:
  reference   the script text itself, as if the speech engine were perfect: measures extraction alone
  asr         transcripts of the author's recordings (clean, and noisy for the held-out lines)
  smoke       transcripts of machine-voice audio (MMS TTS). Plumbing check only; never reported as accuracy

Sets: tune lines may be looked at while adjusting prompts and rules; heldout lines are not, and are reported apart.
"""

import csv
import datetime as _dt
import json
import re
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from . import config
from . import normalize as nz
from .record import FILLED, UNCERTAIN
from .schema import FormSpec, load_forms


def settings() -> dict:
    with open(config.EVAL_DIR / "eval.yaml", encoding="utf-8") as fh:
        s = yaml.safe_load(fh)
    s["today"] = s["today"] if isinstance(s["today"], _dt.date) else _dt.date.fromisoformat(str(s["today"]))
    return s


def load_scripts(lang: str) -> List[dict]:
    with open(config.SCRIPTS_DIR / f"{lang}.yaml", encoding="utf-8") as fh:
        items = yaml.safe_load(fh)
    for it in items:
        it["lang"] = lang
    return items


# ---------------------------------------------------------------- speech metrics

def _words(text: str) -> List[str]:
    t = nz.fold(nz.normalize_text(text))
    return re.sub(r"[.,;:!?\"'()।॥|]", " ", t).split()


def _edit(a: List, b: List) -> int:
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, y in enumerate(b, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y))
        prev = cur
    return prev[-1]


def wer(reference: str, hypothesis: str) -> float:
    """Word error rate after the same normalising on both sides (numbers as digits, folded spelling)."""
    r, h = _words(reference), _words(hypothesis)
    return round(_edit(r, h) / max(1, len(r)), 4)


def cer(reference: str, hypothesis: str) -> float:
    r, h = "".join(_words(reference)), "".join(_words(hypothesis))
    return round(_edit(list(r), list(h)) / max(1, len(r)), 4)


# ---------------------------------------------------------------- field scoring

def same_value(spec, gold, pred) -> bool:
    if pred is None:
        return False
    if spec.type in ("int", "float"):
        try:
            return abs(float(gold) - float(pred)) < 0.01
        except (TypeError, ValueError):
            return False
    if spec.type == "bool":
        return bool(gold) == bool(pred) and isinstance(pred, bool)
    if spec.type == "text" and spec.free_text:
        g, p = set(_words(str(gold))), set(_words(str(pred)))
        return bool(g) and len(g & p) / len(g) >= 0.5
    if spec.type == "text":
        return " ".join(_words(str(gold))) == " ".join(_words(str(pred)))
    return str(gold).strip().upper() == str(pred).strip().upper()


def score_record(form: FormSpec, gold: Dict, record) -> dict:
    """Counts for one utterance. 'to_fix' is what a person would have to change: wrong + missed + spurious."""
    c = {"gold": 0, "correct": 0, "wrong": 0, "missed": 0, "spurious": 0, "uncertain": 0, "errors": []}
    for f in form.fields:
        fv = record.fields.get(f.name)
        pred = fv.value if fv and fv.status in (FILLED, UNCERTAIN) else None
        if fv and fv.status == UNCERTAIN:
            c["uncertain"] += 1
        if f.name in gold:
            c["gold"] += 1
            if same_value(f, gold[f.name], pred):
                c["correct"] += 1
            elif pred is None:
                c["missed"] += 1
                c["errors"].append(f"{f.name}: missed ({gold[f.name]})" + (f" [{fv.note}]" if fv and fv.note else "")
                                   + (f" raw={fv.raw!r}" if fv and fv.raw not in (None, "") else ""))
            else:
                c["wrong"] += 1
                c["errors"].append(f"{f.name}: {pred!r} != {gold[f.name]!r}")
        elif pred is not None:
            c["spurious"] += 1
            c["errors"].append(f"{f.name}: spurious {pred!r}")
    c["to_fix"] = c["wrong"] + c["missed"] + c["spurious"]
    return c


def summarise(rows: List[dict]) -> dict:
    out = {}
    for key in sorted({r["set"] for r in rows}) + ["all"]:
        sub = [r for r in rows if key == "all" or r["set"] == key]
        g = sum(r["gold"] for r in sub)
        out[key] = {
            "utterances": len(sub),
            "field_accuracy": round(sum(r["correct"] for r in sub) / max(1, g), 3),
            "to_fix_per_utterance": round(sum(r["to_fix"] for r in sub) / max(1, len(sub)), 2),
            "spurious": sum(r["spurious"] for r in sub),
            "uncertain": sum(r["uncertain"] for r in sub),
            "all_correct_utterances": sum(1 for r in sub if r["to_fix"] == 0),
            "mean_seconds": round(sum(r["seconds"] for r in sub) / max(1, len(sub)), 2),
        }
    return out


# ---------------------------------------------------------------- runs

def _subset_suffix(sets) -> str:
    """'' for the default tune + heldout run; '_<sets>' when a run covers only some sets, so that it cannot
    overwrite the files of a fuller run (a heldout-only run once replaced the tune rows of six runs)."""
    return "" if set(sets) == {"tune", "heldout"} else "_" + "-".join(sorted(sets))


def _write(run: str, rows: List[dict], summary: dict, meta: dict) -> Path:
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = config.RESULTS_DIR / f"{run}.csv"
    keys = [k for k in rows[0] if k != "errors"] + ["errors"] if rows else []
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({**r, "errors": " | ".join(r.get("errors", []))})
    (config.RESULTS_DIR / f"{run}.summary.json").write_text(
        json.dumps({"meta": meta, "summary": summary}, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_transcripts(name: str) -> Dict[str, str]:
    path = config.RESULTS_DIR / f"{name}.transcripts.json"
    return json.loads(path.read_text(encoding="utf-8"))


def eval_extract(lang: str, route: str, llm=None, condition: str = "reference", sets=("tune", "heldout"),
                 transcripts: Optional[str] = None, limit: Optional[int] = None, verbose: bool = True) -> dict:
    """Field accuracy for one language, one route and one model, on the reference text or on saved transcripts."""
    from .extract import fill

    forms, s = load_forms(), settings()
    texts = load_transcripts(transcripts) if transcripts else None
    items = [it for it in load_scripts(lang) if it["set"] in sets]
    if texts is not None:
        items = [it for it in items if it["id"] in texts]
    else:  # free-speech cards have no script text; they are scored from transcripts only
        items = [it for it in items if it.get("text")]
    items = items[:limit] if limit else items
    rows = []
    for it in items:
        form = forms[it["form"]]
        text = texts[it["id"]] if texts is not None else it["text"]
        rec, info = fill(form, text, lang, route=route, llm=llm, today=s["today"])
        sc = score_record(form, it["gold"], rec)
        rows.append({"id": it["id"], "form": it["form"], "set": it["set"], "seconds": info["seconds"],
                     "prompt_tokens": info.get("prompt_tokens", 0), "completion_tokens": info.get(
                         "completion_tokens", 0), **{k: v for k, v in sc.items()}})
        if verbose:
            print(f"  {it['id']:<11} {sc['correct']}/{sc['gold']} to fix {sc['to_fix']}  {info['seconds']:.1f}s"
                  + ("   " + "; ".join(sc["errors"][:3]) if sc["errors"] else ""))
    model = getattr(llm, "model", "none") if route != "rules" else "none"
    run = f"extract_{lang}_{route}_{re.sub(r'[^A-Za-z0-9.-]+', '-', model)}_{condition}" + _subset_suffix(sets)
    if transcripts:
        run += "_" + transcripts
    summary = summarise(rows)
    meta = {"run": run, "lang": lang, "route": route, "model": model, "condition": condition,
            "transcripts": transcripts, "date": _dt.date.today().isoformat(), "host": _host()}
    _write(run, rows, summary, meta)
    return {"run": run, "summary": summary}


class _PeakRSS:
    """Peak resident memory of this Python process (where the speech model lives) while a block runs."""

    def __enter__(self):
        import psutil

        self.proc, self.peak, self._stop = psutil.Process(), 0, threading.Event()
        self.peak = self.proc.memory_info().rss
        self._t = threading.Thread(target=self._run, daemon=True)
        self._t.start()
        return self

    def _run(self):
        while not self._stop.is_set():
            self.peak = max(self.peak, self.proc.memory_info().rss)
            time.sleep(0.1)

    def __exit__(self, *exc):
        self._stop.set()
        self._t.join()
        self.peak_mb = round(self.peak / 1e6)


def eval_asr(lang: str, backend_name: str, source: str = "recordings", noisy: bool = False,
             sets=("tune", "heldout"), limit: Optional[int] = None, verbose: bool = True) -> dict:
    """Transcribe every script line that has audio, score WER and CER, and save the transcripts for eval_extract.

    source 'recordings': eval/audio/<id>_clean.wav or <id>_noisy.wav, the author's voice.
    source 'smoke':      eval/smoke_audio/<id>.wav, machine voice; noisy adds synthetic noise. Not an accuracy claim.
    """
    from . import audio
    from .asr import get_backend

    s = settings()
    with _PeakRSS() as ram_load:
        backend = get_backend(backend_name)
    items = [it for it in load_scripts(lang) if it["set"] in sets]
    rows, transcripts = [], {}
    with _PeakRSS() as ram_run:
        for it in items:
            if source == "recordings":
                path = config.AUDIO_DIR / f"{it['id']}_{'noisy' if noisy else 'clean'}.wav"
            elif it.get("text"):
                path = config.SMOKE_AUDIO_DIR / f"{it['id']}.wav"
            else:
                continue  # a machine voice cannot speak 'in its own words'
            if not path.exists():
                continue
            wav = audio.load(path)
            if source == "smoke" and noisy:
                wav = audio.add_noise(wav, s["noise_snr_db"], seed=len(rows))
            res = backend.transcribe(wav, lang)
            transcripts[it["id"]] = res.text
            ref = it.get("text")  # free-speech cards have none: no WER, the transcript still feeds eval_extract
            row = {"id": it["id"], "form": it["form"], "set": it["set"], "wer": wer(ref, res.text) if ref else None,
                   "cer": cer(ref, res.text) if ref else None, "seconds": res.seconds,
                   "audio_seconds": res.audio_seconds, "rtf": res.rtf, "hypothesis": res.text}
            rows.append(row)
            if verbose:
                w = f"WER {row['wer']:.2f} CER {row['cer']:.2f}" if ref else "free speech"
                print(f"  {it['id']:<11} {w} RTF {row['rtf']:.2f}  {res.text[:70]}")
            if limit and len(rows) >= limit:
                break
    if not rows:
        raise FileNotFoundError(f"no audio found for {lang} ({source}); see eval/RECORDING.md")
    cond = f"{source}{'-noisy' if noisy else ''}"
    run = f"asr_{lang}_{backend_name}_{cond}" + _subset_suffix(sets)
    summary = {}
    for key in sorted({r["set"] for r in rows}) + ["all"]:
        sub = [r for r in rows if key == "all" or r["set"] == key]
        scored = [r for r in sub if r["wer"] is not None]
        summary[key] = {"utterances": len(sub),
                        "wer": round(sum(r["wer"] for r in scored) / len(scored), 3) if scored else None,
                        "cer": round(sum(r["cer"] for r in scored) / len(scored), 3) if scored else None,
                        "rtf": round(sum(r["rtf"] for r in sub) / len(sub), 3)}
    meta = {"run": run, "lang": lang, "backend": backend_name, "condition": cond, "date": _dt.date.today().isoformat(),
            "ram_after_load_mb": ram_load.peak_mb, "ram_peak_while_transcribing_mb": ram_run.peak_mb,
            "host": _host(), "note": "machine voice, plumbing check only" if source == "smoke" else ""}
    _write(run, rows, summary, meta)
    (config.RESULTS_DIR / f"{run}.transcripts.json").write_text(
        json.dumps(transcripts, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"run": run, "summary": summary, "meta": meta}


def _host() -> str:
    import platform

    import psutil

    return f"{platform.system()} {platform.release()}, {psutil.cpu_count(logical=False)} cores, " \
           f"{round(psutil.virtual_memory().total / 1e9)} GB RAM"


def report() -> Path:
    """results/RESULTS.md from every *.summary.json, newest numbers only, with the condition in each row."""
    rows_x, rows_a = [], []
    for p in sorted(config.RESULTS_DIR.glob("*.summary.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        m, s = d["meta"], d["summary"]
        if m["run"].startswith("extract_"):
            for key in ("tune", "heldout", "free"):
                if key in s:
                    v = s[key]
                    rows_x.append(f"| {m['lang']} | {m['route']} | {m['model']} | {m['condition']}"
                                  f"{' (' + m['transcripts'] + ')' if m.get('transcripts') else ''} | {key} | "
                                  f"{v['utterances']} | {v['field_accuracy']:.3f} | {v['to_fix_per_utterance']} | "
                                  f"{v['all_correct_utterances']} | {v['mean_seconds']} | {m['date']} |")
        else:
            for key in ("tune", "heldout", "free"):
                if key in s:
                    v = s[key]
                    w = "n/a" if v["wer"] is None else f"{v['wer']:.3f}"
                    c = "n/a" if v["cer"] is None else f"{v['cer']:.3f}"
                    rows_a.append(f"| {m['lang']} | {m['backend']} | {m['condition']} | {key} | {v['utterances']} | "
                                  f"{w} | {c} | {v['rtf']:.3f} | {m['ram_after_load_mb']} | "
                                  f"{m['date']} | {m.get('note') or ''} |")
    lines = ["# Results", "", "Written by `python -m voiceform report` from results/*.summary.json. A row exists only if a",
             "script produced it on the named device (see each summary file). Scripts drafted by Claude and not yet",
             "reviewed by the author; dates resolve against eval/eval.yaml.", "",
             "## Extraction (field accuracy)", "",
             "| Lang | Route | Model | Condition | Set | Utterances | Field accuracy | To fix per utterance | "
             "All correct | Seconds per utterance | Date |",
             "|---|---|---|---|---|---|---|---|---|---|---|", *rows_x, "",
             "## Speech to text", "",
             "| Lang | Backend | Condition | Set | Utterances | WER | CER | RTF | RAM after load (MB) | Date | Note |",
             "|---|---|---|---|---|---|---|---|---|---|---|", *rows_a, ""]
    path = config.RESULTS_DIR / "RESULTS.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
