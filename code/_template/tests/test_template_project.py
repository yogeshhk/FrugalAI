"""Offline test for the stub: no model server, no download. Every failure you find in your project becomes a test like this."""

from frugalai_common.llm import ScriptedChat

from template_project.core import Assistant, load_settings, route


def test_the_core_class_uses_code_first_and_the_model_otherwise():
    bot = Assistant(llm=ScriptedChat(["Paris."]))
    assert bot.answer("2 + 3") == "5"
    assert bot.answer("Capital of France?") == "Paris."


def test_settings_come_from_config_yaml():
    assert load_settings()["llm"]["kind"] in ("http", "llama_cpp", "fake")


def test_arithmetic_is_routed_to_code():
    assert route("2 + 3") == "calc"
    assert route("12 * (3 + 4) =") == "calc"


def test_a_plain_question_is_a_lookup():
    assert route("When is the bill due?") == "lookup"


def test_a_bare_number_is_not_a_calculation():
    assert route("2024") == "lookup"
