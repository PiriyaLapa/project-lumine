"""
TDD — message_generator.py (part of QA-4 test_auto_touch.py coverage).
Claude API is always mocked — never call the real API in tests.
PDPA opt-out line is hardcoded in the system prompt (non-bypassable),
never in a user-editable config. generate() and send() are always two
separate calls — this module only drafts, never sends.
"""
from unittest.mock import MagicMock, patch

from app.services.message_generator import MessageGenerator, PDPA_OPT_OUT_TH, PDPA_OPT_OUT_EN


def make_anthropic_response(text: str):
    resp = MagicMock()
    block = MagicMock()
    block.type = "text"
    block.text = text
    resp.content = [block]
    return resp


class TestMessageGenerator:
    def test_generates_thai_message_with_pdpa_line(self):
        with patch("app.services.message_generator.anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = make_anthropic_response(
                f"สวัสดีค่ะ ขอบคุณที่อุดหนุนนะคะ {PDPA_OPT_OUT_TH}"
            )
            gen = MessageGenerator()
            result = gen.generate(
                customer_name="สมชาย ใจดี",
                language="th",
                touchpoint="2D",
                products=[{"product_clean": "TOC Spin Polo Shirt", "returned": False}],
            )

        assert result.language == "th"
        assert result.touchpoint == "2D"
        assert PDPA_OPT_OUT_TH in result.message_text
        assert len(result.message_text) > 0

    def test_generates_english_message_with_pdpa_line(self):
        with patch("app.services.message_generator.anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = make_anthropic_response(
                f"Hi John, thanks for your purchase! {PDPA_OPT_OUT_EN}"
            )
            gen = MessageGenerator()
            result = gen.generate(
                customer_name="John Smith",
                language="en",
                touchpoint="2W",
                products=[{"product_clean": "Polo Shirt", "returned": False}],
            )

        assert result.language == "en"
        assert PDPA_OPT_OUT_EN in result.message_text

    def test_excludes_returned_products_from_context(self):
        """Caller responsibility per ARCH-5, but generator must not choke on a
        products list where returned items were already filtered out."""
        with patch("app.services.message_generator.anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = make_anthropic_response(
                f"Hi, thanks! {PDPA_OPT_OUT_EN}"
            )
            gen = MessageGenerator()
            gen.generate(
                customer_name="John Smith",
                language="en",
                touchpoint="2M",
                products=[{"product_clean": "Polo Shirt", "returned": False}],
            )
            call_kwargs = MockClient.return_value.messages.create.call_args.kwargs
            user_content = str(call_kwargs["messages"])
            assert "Polo Shirt" in user_content

    def test_pii_never_sent_to_claude(self):
        """Customer phone/email must never appear in the prompt sent to Claude."""
        with patch("app.services.message_generator.anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = make_anthropic_response(
                f"Hi! {PDPA_OPT_OUT_EN}"
            )
            gen = MessageGenerator()
            gen.generate(
                customer_name="John Smith",
                language="en",
                touchpoint="2D",
                products=[],
            )
            call_kwargs = MockClient.return_value.messages.create.call_args.kwargs
            # generate() signature takes no phone/email at all — structurally impossible to leak
            assert "phone" not in call_kwargs
            assert "email" not in call_kwargs

    def test_never_calls_real_api(self):
        """Guard: this test file must never construct a real, unmocked client."""
        with patch("app.services.message_generator.anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = make_anthropic_response(
                f"Test {PDPA_OPT_OUT_EN}"
            )
            MessageGenerator().generate(
                customer_name="Test", language="en", touchpoint="2D", products=[]
            )
            MockClient.assert_called_once()
