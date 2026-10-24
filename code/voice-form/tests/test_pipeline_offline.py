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
