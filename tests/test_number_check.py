"""Tests for the 'invented number' safety check."""

from agent.number_check import find_unverified_numbers

TOOL_RESULT = {"eGFR": {"n": 288, "missing": 15, "mean": 55.0, "median": 56.6,
                        "q1": 41.18, "q3": 69.03, "min": 5.0, "max": 107.0}}


def test_copied_numbers_are_fine_even_when_rounded():
    answer = "n = 288, mean 55.0, median 56.6, Q1 41.2, Q3 69.0, range 5.0 to 107."
    assert find_unverified_numbers(answer, [TOOL_RESULT]) == []


def test_number_calculated_by_the_ai_is_caught():
    # 69.03 - 41.18 = 27.85: the AI did maths itself. This happened in a real test run.
    answer = "Q1 = 41.2, Q3 = 69.0 (IQR = 27.8)."
    assert find_unverified_numbers(answer, [TOOL_RESULT]) == ["27.8"]


def test_category_names_like_G3b_are_not_numbers():
    assert find_unverified_numbers("Most patients are in stage G3b.", [TOOL_RESULT]) == []


def test_numbers_from_the_question_are_allowed():
    assert find_unverified_numbers("Patients over 65 ...", [], question="age over 65") == []
