"""IntentRouter (core.py) and the config loader. Offline: fake loader and scorer, no torch, no model."""

import json

from ftslm import config
from ftslm.core import IntentRouter

CSV = ("system,split,accuracy,prompt_tokens_mean,date\n"
       "base_few_shot,test_ood,0.42,205.6,2026-10-21\n"
       "tuned,test_ood,0.92,18.6,2026-10-21\n")


def _settings(tmp_path, **over):
    (tmp_path / "data").mkdir()
    rows = [{"text": "t " + lab, "label": lab} for lab in ("weather", "price", "pest", "scheme", "repair", "other")]
    (tmp_path / "data" / "train.jsonl").write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    (tmp_path / "log.json").write_text(json.dumps({"train_seconds": 1311, "adapter_mb": 3.72}), encoding="utf-8")
    (tmp_path / "results.csv").write_text(CSV, encoding="utf-8")
    s = {**config.DEFAULTS, "model": "fake-model", "adapter": str(tmp_path / "adapter"), "data_dir": str(tmp_path / "data"),
         "train_log": str(tmp_path / "log.json"), "results_csv": str(tmp_path / "results.csv"), "messages": ["a", "b"]}
    return {**s, **over}


def _router(tmp_path, **over):
    calls = []

    def loader(model_id, adapter, threads):
        calls.append((model_id, adapter, threads))
        return ("tok", "tuned" if adapter else "base")

    def scorer(tok, model, prompts):
        return (["pest" if model == "tuned" else "other"], {"prompt_tokens_mean": float(len(prompts[0]))})

    return IntentRouter(_settings(tmp_path, **over), loader=loader, scorer=scorer), calls


def test_classify_runs_both_systems_and_loads_once(tmp_path):
    r, calls = _router(tmp_path)
    assert not r.loaded
    base, tuned = r.classify("white spots on the onion")
    assert (base.system, base.label) == ("base", "other") and (tuned.system, tuned.label) == ("tuned", "pest")
    assert base.prompt_tokens > tuned.prompt_tokens        # the instruction and examples make the base prompt longer
    assert "6 examples" in base.title and "22 minutes" in tuned.title and "3.7 MB" in tuned.title
    r.classify("again")
    assert [c[1] is None for c in calls] == [True, False] and r.loaded    # one base load, one adapter load, no more


def test_settings_reach_the_loader(tmp_path):
    r, calls = _router(tmp_path, threads=3)
    r.load()
    assert calls[0] == ("fake-model", None, 3) and calls[1][0] == "fake-model" and calls[1][2] == 3


def test_page_data_without_a_model(tmp_path):
    r, calls = _router(tmp_path)
    assert r.messages == ["a", "b"] and "weather" in r.labels
    m = r.measured()
    assert (m.few_shot_accuracy, m.tuned_accuracy, m.date) == (0.42, 0.92, "2026-10-21")
    assert not calls                                       # none of that needs a model


def test_missing_log_and_results_are_not_errors(tmp_path):
    r, _ = _router(tmp_path, train_log=str(tmp_path / "none.json"), results_csv=str(tmp_path / "none.csv"))
    assert r.train_log() == {} and r.tuned_title() == "Fine-tuned (LoRA)" and r.measured() is None


def test_load_settings_defaults_file_and_resolve(tmp_path):
    assert config.load_settings(tmp_path / "missing.yaml")["adapter"] == "adapters/intent"
    f = tmp_path / "c.yaml"
    f.write_text("model: other/model\nmessages: [x]\n", encoding="utf-8")
    s = config.load_settings(f)
    assert s["model"] == "other/model" and s["messages"] == ["x"] and s["data_dir"] == "data"   # unset keys keep defaults
    assert config.resolve("adapters/intent") == config.ROOT / "adapters" / "intent"
    assert config.resolve(tmp_path) == tmp_path


def test_shipped_config_matches_the_trained_adapter():
    s = config.load_settings()
    assert s["model"] == "HuggingFaceTB/SmolLM2-135M-Instruct" and len(s["messages"]) > 0
    assert config.resolve(s["adapter"]).is_dir() and config.resolve(s["train_log"]).is_file()
