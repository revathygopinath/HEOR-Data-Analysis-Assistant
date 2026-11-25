"""A simple safety check: did the AI write any number that no tool produced?

The AI is told never to calculate. But AIs sometimes do it anyway
(for example, "IQR = 27.8" by subtracting Q1 from Q3 in its head).
This check does not trust the AI. It:
  1. collects every number that appeared in the tool results (and the question),
  2. finds every number in the AI's answer,
  3. lists the answer's numbers that are NOT in step 1.

The app then shows a warning, so a human can check those numbers.
It is a simple text check, not perfect, but it catches most invented numbers.
"""

import json
import re

# Finds numbers like 55, 55.0, -3.2, 1,234 (but not the "3" inside "G3b").
_NUMBER = re.compile(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?(?![\w])")


def _numbers_in(text: str) -> list[float]:
    found = []
    for match in _NUMBER.findall(text):
        try:
            found.append(float(match.replace(",", "")))
        except ValueError:
            pass
    return found


def _allowed_forms(value: float) -> set[float]:
    """55.034 may be written as 55.03, 55.0 or 55 by the AI. All of these are fine."""
    return {round(value, 2), round(value, 1), float(round(value))}


def find_unverified_numbers(answer: str, tool_results: list[dict], question: str = "") -> list[str]:
    allowed = set()
    for result in tool_results:
        for value in _numbers_in(json.dumps(result, default=str)):
            allowed |= _allowed_forms(value)
    for value in _numbers_in(question):
        allowed |= _allowed_forms(value)

    unverified = []
    for text_number in _NUMBER.findall(answer):
        value = float(text_number.replace(",", ""))
        if value.is_integer() and 0 <= value <= 10:
            continue            # small whole numbers ("3 tools", "step 1") are too common to check
        if round(value, 2) not in allowed and round(value, 1) not in allowed:
            unverified.append(text_number)
    return sorted(set(unverified))
