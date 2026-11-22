"""VoiceForm (core.py), the config file and the sink registry. Offline: fakes only, no server, no model."""

import datetime as dt
import shutil

import numpy as np
import pytest

from voiceform import audio, config, sinks
from voiceform.asr import FakeASR
from voiceform.core import VoiceForm
from voiceform.llm import FakeLLM
from voiceform.record import FILLED, MISSING

TODAY = dt.date(2026, 10, 31)
SAID = "नाव हरी गावडे. गाव मोरगाव. मोबाईल नऊ चार शून्य चार शून्य चार शून्य चार एक एक. मोटर खूप आवाज करते. लगेच या."


def _reply(form, **vals):
    return {n: {"value": vals.get(n, (None, None))[0], "evidence": vals.get(n, (None, None))[1]} for n in form.names}


def _ticket(vf):
    return _reply(vf.forms["service_ticket"], customer_name=("हरी गावडे", "हरी गावडे"), village=("मोरगाव", "गाव मोरगाव"),
                  phone=("9404040411", "x"), product=("water_pump", "मोटर"),
                  problem=("मोटर खूप आवाज करते", "मोटर खूप आवाज करते"), urgency=("high", "लगेच"))


def _vf(tmp_path, replies=None, asr=None):
    vf = VoiceForm(llm=FakeLLM(replies or [{}]), asr=asr, outbox=tmp_path, today=TODAY)
    vf.start("service_ticket", "mr")
    return vf


def test_core_fills_a_form_from_text_and_saves_only_when_valid(tmp_path):
    vf = _vf(tmp_path)
    vf._fixed_llm.replies = [_ticket(vf)]
    assert not vf.can_save() and "customer_name" in vf.still_needed()
    turn = vf.read(SAID)
    assert turn.blocked_connections == 0 and not turn.followup
    rows = {r.name: r for r in vf.rows()}
    assert rows["phone"].status == FILLED and rows["phone"].value == "9404040411"
    assert rows["under_warranty"].status == MISSING and rows["under_warranty"].value == ""
    assert vf.can_save()
    saved = vf.confirm_and_save()
    assert set(saved) == set(config.SINKS) and all(p.exists() for p in saved.values())
    assert not vf.can_save()                                   # saved once; a new record starts again


def test_core_merges_a_follow_up_into_the_same_record(tmp_path):
    vf = _vf(tmp_path)
    form = vf.forms["service_ticket"]
    vf._fixed_llm.replies = [_reply(form, customer_name=("हरी गावडे", "हरी गावडे")),
                             _reply(form, village=("मोरगाव", "गाव मोरगाव"))]
    vf.read("नाव हरी गावडे")
    turn = vf.read("गाव मोरगाव")
    assert turn.followup and turn.changed == ["village"]
    assert vf.changed_labels() == [form.get("village").label_in("en")]
    assert {r.name: r.value for r in vf.rows()}["customer_name"] == "हरी गावडे"   # kept from the first utterance


def test_core_hears_audio_through_the_speech_backend(tmp_path):
    vf = _vf(tmp_path, asr=FakeASR([SAID]))
    vf._fixed_llm.replies = [_ticket(vf)]
    turn = vf.hear(np.zeros(16000, dtype=np.float32), source="sample mr-01")
    assert turn.transcript == SAID and turn.timings["audio_seconds"] == 1.0 and vf.source == "sample mr-01"


def test_core_refuses_to_save_an_invalid_record(tmp_path):
    vf = _vf(tmp_path)
    vf.read("नाव हरी गावडे")                                   # the fake model returns nothing
    with pytest.raises(sinks.InvalidRecord):
        vf.confirm_and_save()
    assert not any(tmp_path.iterdir())


def test_core_needs_a_form_first(tmp_path):
    with pytest.raises(RuntimeError, match="start"):
        VoiceForm(llm=FakeLLM([{}])).read("x")
    with pytest.raises(KeyError):
        VoiceForm(llm=FakeLLM([{}])).start("no_such_form", "mr")


def test_rules_route_needs_no_model(tmp_path):
    vf = VoiceForm(route="rules", outbox=tmp_path, today=TODAY)   # no llm given and none built
    vf.start("service_ticket", "mr")
    vf.read(SAID)
    assert {r.name: r.status for r in vf.rows()}["phone"] == FILLED
    assert vf._llms == {}


def test_config_file_is_read_and_missing_keys_fall_back(tmp_path):
    cfg = tmp_path / "c.yaml"
    cfg.write_text("asr: whisper-base\nllm:\n  kind: llama_cpp\n  gguf: m.gguf\n", encoding="utf-8")
    s = config.load_settings(cfg)
    assert s["asr"] == "whisper-base" and s["llm"]["kind"] == "llama_cpp" and s["llm"]["gguf"] == "m.gguf"
    assert s["route"] == "direct" and s["llm"]["model"] == "qwen/qwen3-1.7b"   # from the defaults
    assert config.load_settings(tmp_path / "missing.yaml")["sinks"] == ["form", "sqlite", "crm", "api"]


def test_the_shipped_config_names_real_choices():
    assert config.ASR_NAME in config.ASR_MODELS
    assert config.ROUTE in ("rules", "direct", "translate")
    assert set(config.SINKS) <= set(sinks.SINKS)
    assert config.LLM_KIND in ("http", "llama_cpp", "fake")


def test_unknown_sink_is_refused(tmp_path):
    vf = _vf(tmp_path)
    vf._fixed_llm.replies = [_ticket(vf)]
    vf.read(SAID)
    vf.turn.record.confirmed = True
    with pytest.raises(ValueError, match="unknown sink"):
        sinks.send(vf.turn.record, vf.form, sinks=["cloud"], outbox=tmp_path)


def test_wav_is_read_without_ffmpeg(tmp_path, monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda name: None)   # as on a phone: no ffmpeg program
    tone = (0.3 * np.sin(2 * np.pi * 440 * np.arange(16000) / 16000)).astype(np.float32)
    path = audio.save_wav(tmp_path / "t.wav", tone)
    back = audio.load(path)
    assert len(back) == 16000 and np.max(np.abs(back - tone)) < 1e-3
    assert len(audio.load_bytes(path.read_bytes())) == 16000
    from scipy.io import wavfile

    stereo = np.stack([tone, tone], axis=1)
    wavfile.write(str(tmp_path / "s.wav"), 48000, (stereo * 32767).astype(np.int16))
    assert abs(len(audio.load(tmp_path / "s.wav")) - 16000 / 3) < 2          # 1/3 s at 48 kHz -> 16 kHz mono
    with pytest.raises(RuntimeError, match="ffmpeg"):
        audio.load_bytes(b"not a wav file")
