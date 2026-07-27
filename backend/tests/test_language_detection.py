"""
TDD — language_detection.py (QA-5).
Sprint 1 architect decision: Unicode-range detection only. Anything not
containing Thai script defaults to 'en' — no romanization/surname
heuristic. language_source is set by the caller, not this function.
"""
from app.services.language_detection import detect_language


class TestDetectLanguage:
    def test_pure_thai_script_name(self):
        assert detect_language("สมชาย ใจดี") == "th"

    def test_pure_english_name(self):
        assert detect_language("John Smith") == "en"

    def test_romanized_thai_name_defaults_to_en(self):
        """Architect decision: no heuristic for romanized Thai — defaults to 'en'."""
        assert detect_language("Somchai Jaidee") == "en"

    def test_mixed_script_name_with_any_thai_char_is_th(self):
        assert detect_language("John สมชาย") == "th"

    def test_thai_name_with_english_suffix(self):
        assert detect_language("สมชาย Mr.") == "th"

    def test_empty_string_defaults_to_en(self):
        assert detect_language("") == "en"

    def test_whitespace_only_defaults_to_en(self):
        assert detect_language("   ") == "en"

    def test_name_with_numbers_defaults_to_en(self):
        assert detect_language("Customer 12345") == "en"

    def test_all_caps_english_name(self):
        assert detect_language("JOHN SMITH") == "en"

    def test_ambiguous_initials_only(self):
        assert detect_language("J. S.") == "en"
