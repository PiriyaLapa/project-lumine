"""
Message Generator — drafts a personalized Auto-Touch message via Claude API.

Draft only — never sends. generate-message and send are always two
separate calls (PM rule: auto-send without human approval is permanently
excluded). The PDPA opt-out line is hardcoded here, in the system
prompt, deliberately not loaded from any JSON config an associate or
future dev could edit without review.

No DB/Session import — this service is stateless per ARCH-5.
"""
import logging
from dataclasses import dataclass

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)

_MODEL = "claude-opus-4-8"

PDPA_OPT_OUT_TH = "หากไม่ต้องการรับข้อความลักษณะนี้อีก แจ้งเราได้เลยค่ะ"
PDPA_OPT_OUT_EN = "Reply STOP anytime if you'd prefer not to receive these messages."

_SYSTEM_PROMPT_TH = f"""คุณเป็นผู้ช่วยร่างข้อความติดตามลูกค้าให้พนักงานขายร้าน Hugo Boss
เขียนข้อความสั้น เป็นกันเอง และจริงใจ ไม่เกิน 3-4 ประโยค
ห้ามเขียนขายของตรงๆ หรือดูเหมือนสแปม
ต้องจบข้อความด้วยประโยคนี้เสมอ (ห้ามแก้ไขหรือละเว้น): "{PDPA_OPT_OUT_TH}\""""

_SYSTEM_PROMPT_EN = f"""You draft short, warm follow-up messages for a Hugo Boss sales associate.
Keep it to 3-4 sentences, personal, never salesy or spammy.
You must always end the message with exactly this sentence (never edit or omit it): "{PDPA_OPT_OUT_EN}\""""

_TOUCHPOINT_CONTEXT = {
    "2D": "This is a check-in 2 days after purchase — ask how the item is working out.",
    "2W": "This is a relationship-building touch 2 weeks after purchase — no ask, just staying in touch.",
    "2M": "This is a retention check 2 months after purchase — gently invite them back.",
}


@dataclass
class GenerateMessageResult:
    message_text: str
    language: str
    touchpoint: str


class MessageGenerator:
    def __init__(self):
        self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def generate(
        self, customer_name: str, language: str, touchpoint: str, products: list[dict]
    ) -> GenerateMessageResult:
        system_prompt = _SYSTEM_PROMPT_TH if language == "th" else _SYSTEM_PROMPT_EN
        product_names = ", ".join(p["product_clean"] for p in products) or "their recent purchase"
        touchpoint_context = _TOUCHPOINT_CONTEXT.get(touchpoint, "")

        user_prompt = (
            f"Customer name: {customer_name}\n"
            f"Product(s): {product_names}\n"
            f"Context: {touchpoint_context}"
        )

        response = self._client.messages.create(
            model=_MODEL,
            max_tokens=512,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        message_text = next((b.text for b in response.content if b.type == "text"), "")
        logger.info("message_generator: drafted message touchpoint=%s language=%s", touchpoint, language)
        return GenerateMessageResult(message_text=message_text, language=language, touchpoint=touchpoint)
