"""Tech Observer — Big Tech news, AI model releases, breakthrough technologies."""
from .base_observer import BaseObserver

SYSTEM = """You are an AI Tech Observer agent. Your job is to produce a precise, \
up-to-date summary of the most significant technology developments in the AI space.

Cover:
• New AI model releases (versions, benchmarks, capabilities) — OpenAI, Anthropic, Google, Meta, Mistral, xAI, etc.
• Big Tech company announcements (Google, Microsoft, Apple, Amazon, Meta, NVIDIA, etc.)
• Breakthrough research papers and technical achievements
• New AI products, applications, and platform launches
• AI infrastructure — chips, data centres, cloud AI services
• Open-source model releases and community milestones
• Security, safety, and alignment developments
• Notable acquisitions and talent moves in tech

Instructions:
1. Search the web for AI and Big Tech news around the review date.
2. Be specific: model names, version numbers, benchmark scores, company names.
3. Return ONLY a valid JSON array of exactly 20 objects — nothing else.
   Each object must have:
   - "title"      : concise headline, max 15 words
   - "details"    : 2-3 sentences with concrete technical facts
   - "category"   : one of: new_model | breakthrough | big_tech | research | product | infrastructure | open_source | acquisition
   - "importance" : "high" | "medium" | "low"
   - "sources"    : array of 1-3 objects, each with "label" (publication name) and "url" (direct link to article)
"""

USER_TEMPLATE = """\
Review date: {review_date}

Search for AI and Big Tech news around this date and return 20 NEW, UNIQUE insights.

PREVIOUSLY COVERED TOPICS — do NOT repeat any of these:
{history_block}

Generate 20 fresh tech insights not listed above.
Return ONLY the JSON array. No markdown, no extra text."""


class TechObserver(BaseObserver):
    section_id = "tech"

    def build_prompts(self, history: list[str], review_date: str) -> tuple[str, str]:
        history_block = (
            "\n".join(f"• {t}" for t in history[-100:])
            if history else "(none — this is the first run)"
        )
        return SYSTEM, USER_TEMPLATE.format(
            review_date=review_date,
            history_block=history_block,
        )
