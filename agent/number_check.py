"""A simple safety check: did the AI write any number that no tool produced?

The AI is told never to calculate. But AIs sometimes do it anyway
(for example, "IQR = 27.8" by subtracting Q1 from Q3 in its head).
This check does not trust the AI. It:
  1. collects every number that appeared in the tool results (and the question),
  2. finds every number in the AI's answer,
  3. lists the answer's numbers that are NOT in step 1.

Rounding is allowed: if a tool said 14.65 and the AI wrote 14.7 (one decimal),
that is fine, because 14.65 is within 0.05 of 14.7.

The app then shows a warning, so a human can check those numbers.
It is a simple text check, not perfect, but it catches most invented numbers.
"""

import json
import re

# Finds numbers like 55, 55.0, -3.2, 1,234 and also "1.73" inside "1.73m".
# It skips digits that are part of a word, like the "3" in "G3b" or "eGFR2".
_NUMBER = re.compile(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?(?![\d])")


def _numbers_in(text: str) -> list[float]:
    found = []
    for match in _NUMBER.findall(text):
        try:
            found.append(float(match.replace(",", "")))
        except ValueError:
            pass
    return found


def _matches_after_rounding(written: str, sources: list[float]) -> bool:
    """True if the written number is one of the source numbers, maybe rounded.

    "14.7" has 1 decimal place, so any source between 14.65 and 14.75 is OK.
    "59" has 0 decimal places, so any source between 58.5 and 59.5 is OK.
    """
    value = float(written.replace(",", ""))
    decimals = len(written.split(".")[1]) if "." in written else 0
    tolerance = 0.5 * 10 ** -decimals + 1e-9
    return any(abs(source - value) <= tolerance for source in sources)


def find_unverified_numbers(answer: str, tool_results: list[dict], question: str = "") -> list[str]:
    sources = []
    for result in tool_results:
        sources += _numbers_in(json.dumps(result, default=str))
    sources += _numbers_in(question)

    unverified = []
    for written in _NUMBER.findall(answer):
        value = float(written.replace(",", ""))
        if value.is_integer() and 0 <= value <= 10:
            continue            # small whole numbers ("3 tools", "step 1") are too common to check
        if not _matches_after_rounding(written, sources):
            unverified.append(written)
    return sorted(set(unverified))