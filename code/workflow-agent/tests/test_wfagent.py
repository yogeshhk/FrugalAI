"""Offline tests: scripted fake model, no server. Run from the repo root: pytest code/workflow-agent/tests -v"""

import tempfile

from wfagent import knowledge as K
from wfagent.evaluate import evaluate, judge, load_cases
from wfagent.graph import TOOLS, build_graph, reply_problems, run_message
from wfagent.llm import FakeLLM, strip_think


def test_slot_extraction():
    s = K.extract_slots("What is the price of wheat in Pune market today?")
    assert (s["crop"], s["place"], s["day"]) == ("wheat", "pune", "today")
    assert K.extract_slots("Is a storm coming to Nashik tomorrow?")["day"] == "tomorrow"
    assert K.extract_slots("My tractor will not start")["tool"] == "tractor"


def test_tools_return_table_rows_or_not_found():
    assert "2450" in TOOLS["price"]({"crop": "wheat", "place": "pune"})
    assert TOOLS["price"]({"crop": "saffron", "place": "pune"}).startswith(K.NOT_FOUND)
    assert TOOLS["weather"]({"place": "kolhapur", "day": "today"}).startswith(K.NOT_FOUND)


def test_check_rejects_invented_numbers_and_empty_replies():
    facts = "wheat at Pune: 2450 rupees per quintal"
    assert reply_problems("Wheat is 2450 rupees per quintal.", facts, "price of wheat?") == []
    assert any("invented" in p for p in reply_problems("It is 2500 rupees.", facts, "price of wheat?"))
    assert reply_problems("", facts, "x")


def test_every_case_is_routed_correctly_by_the_rules():
    for case in load_cases():
        assert K.rule_intent(case["message"]) == case["intent"], case["id"]


def test_graph_end_to_end_with_fake_model():
    llm = FakeLLM("good")
    out = run_message(build_graph(llm), llm, "What is the price of wheat in Pune market today?")
    assert out["intent"] == "price" and "2450" in out["reply"] and not out["fallback"]
    assert out["cost"]["llm_calls"] == 2          # classify once, compose once


def test_hallucinated_reply_is_caught_and_retried():
    llm = FakeLLM("hallucinate_first")
    out = run_message(build_graph(llm), llm, "What is the price of wheat in Pune market today?")
    assert "9999" not in out["reply"] and "2450" in out["reply"]
    assert out["cost"]["llm_calls"] == 3          # classify, bad compose, good compose
    assert any("invented number" in t for t in out["trace"])


def test_fallback_when_model_keeps_failing():
    class Stubborn(FakeLLM):
        def __call__(self, prompt, max_tokens=None):
            if "FACTS:" in prompt:
                self.calls += 1
                return "It costs 12345 rupees."
            return super().__call__(prompt, max_tokens)

    llm = Stubborn()
    out = run_message(build_graph(llm), llm, "What is the price of wheat in Pune market today?")
    assert out["fallback"] and "2450" in out["reply"] and "12345" not in out["reply"]


def test_judge_flags_invented_numbers():
    case = {"message": "What is the price of wheat in Pune?", "intent": "price", "facts": ["2450"]}
    assert judge(case, "Wheat is 2450 rupees.", "price")["success"]
    assert not judge(case, "Wheat is 2450 rupees, up 5 percent.", "price")["success"]
    assert not judge(case, "Wheat is 2450 rupees.", "weather")["success"]


def test_evaluate_on_fake_model_scores_perfectly_and_writes_files():
    with tempfile.TemporaryDirectory() as tmp:
        rows, _ = evaluate(FakeLLM("good"), systems=("workflow",), out_dir=tmp, log=lambda *_: None)
        assert rows[0]["success_rate"] == 1.0 and rows[0]["invented_number_rate"] == 0.0


def test_strip_think():
    assert strip_think("<think>hmm</think>\nprice") == "price"
