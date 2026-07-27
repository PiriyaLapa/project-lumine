"""
Language Detection — pure function, no DB dependency.

Sprint 1 architect decision: Thai Unicode-range detection only. Any name
containing at least one Thai-script character is 'th'; everything else
(including romanized Thai names) defaults to 'en'. This is a deliberate
simplification, not a general-purpose language classifier — a fuller
romanization heuristic was explicitly deferred out of Sprint 1.
"""

_THAI_RANGE_START = "฀"
_THAI_RANGE_END = "๿"


def detect_language(name: str) -> str:
    """Return 'th' if any character in name is in the Thai Unicode block, else 'en'."""
    for ch in name:
        if _THAI_RANGE_START <= ch <= _THAI_RANGE_END:
            return "th"
    return "en"
