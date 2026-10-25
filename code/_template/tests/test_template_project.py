"""Offline test for the stub: no model server, no download. Every failure you find in your project becomes a test like this."""

from template_project.core import route


def test_arithmetic_is_routed_to_code():
    assert route("2 + 3") == "calc"
    assert route("12 * (3 + 4) =") == "calc"


def test_a_plain_question_is_a_lookup():
    assert route("When is the bill due?") == "lookup"


def test_a_bare_number_is_not_a_calculation():
    assert route("2024") == "lookup"
