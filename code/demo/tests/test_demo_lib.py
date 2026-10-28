"""Offline tests for the demo helpers: no LM Studio, no network."""

import json
import socket
import threading

import pytest

import demo_lib as D


def test_question_rules_are_fixed_and_ordered():
    heldout = [{"id": "a", "kind": "cross", "q": "q1"}, {"id": "b", "kind": "status", "q": "q2"},
               {"id": "c", "kind": "status", "q": "q3"}, {"id": "d", "kind": "unanswerable", "q": "q4"},
               {"id": "e", "kind": "lookup", "q": "q5"}]
    got = D.qwiki_questions(heldout)
    assert [q["id"] for q in got] == ["b", "a", "d"]                 # first of each kind, in the fixed kind order, lookup left out


def test_marathi_rule_takes_first_two_per_group():
    tests = [{"id": "r%d" % i, "group": "reworded"} for i in range(4)] + [{"id": "c1", "group": "control"}]
    got = D.marathi_questions(tests)
    assert [q["id"] for q in got] == ["r0", "r1", "c1"]


def test_key_hit_matches_the_study_rule():
    assert D.key_hit("अन्न आणि कपडे आणि निवारा", ["अन्न", "वस्त्र|कपडे", "निवारा"])
    assert not D.key_hit("अन्न आणि निवारा", ["अन्न", "वस्त्र|कपडे", "निवारा"])
    assert not D.key_hit("anything", [])


def test_devanagari_share():
    assert D.devanagari_share("नमस्कार") == 1.0
    assert D.devanagari_share("abc") == 0.0
    assert D.devanagari_share("") == 0.0


def test_load_recorded_missing_file_is_empty(tmp_path):
    assert D.load_recorded(tmp_path, "base_closed") == {}


def test_load_recorded_reads_rows(tmp_path):
    (tmp_path / "mr_answers_base_closed.jsonl").write_text(
        json.dumps({"id": "e1_01", "answer": "x"}, ensure_ascii=False) + "\n", encoding="utf-8")
    assert D.load_recorded(tmp_path, "base_closed")["e1_01"]["answer"] == "x"


def test_model_status_all_false_when_server_down(monkeypatch):
    monkeypatch.setattr(D, "loaded_models", lambda: None)
    assert D.model_status() == {"chat": False, "embedding": False, "marathi": False}


def test_guard_blocks_other_hosts_and_counts_local():
    g = D.Guard()
    original = (socket.socket.connect, socket.socket.connect_ex)
    try:
        D.install_guard(g)
        s = socket.socket()
        with pytest.raises(D.Blocked):
            s.connect(("93.184.216.34", 80))                      # an internet address: refused before any packet is sent
        assert s.connect_ex(("93.184.216.34", 80)) == 111
        assert g.blocked and g.blocked[0][0] == "93.184.216.34"
        server = socket.socket()
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        threading.Thread(target=server.accept, daemon=True).start()
        c = socket.socket()
        c.connect(("127.0.0.1", server.getsockname()[1]))
        assert g.local == 1
        c.close()
        server.close()
        s.close()
    finally:
        socket.socket.connect, socket.socket.connect_ex = original
