"""Tech Observer — Big Tech news, AI model releases, breakthrough technologies."""
from datetime import datetime
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
1. Search the web for AI and Big Tech news from the last 7–14 days.
2. Be specific: model names, version numbers, benchmark scores, company names, dates.
3. Return ONLY a valid JSON array of exactly 20 objects — nothing else.
   Each object must have:
   - "title"      : concise headline, max 15 words
   - "details"    : 2-3 sentences with concrete technical facts
   - "category"   : one of: new_model | breakthrough | big_tech | research | product | infrastructure | open_source | acquisition
   - "importance" : "high" | "medium" | "low"
"""

USER_TEMPLATE = """\
Today is {date}.

Search for the latest AI and Big Tech news and return 20 NEW, UNIQUE insights.

PREVIOUSLY COVERED TOPICS — do NOT repeat any of these:
{history_block}

Generate 20 fresh tech insights that differ from everything above.
Return ONLY the JSON array. No markdown, no explanation text."""


class TechObserver(BaseObserver):
    section_id = "tech"
    history_filename = "tech_history.json"

    def build_prompts(self, history: list[str]) -> tuple[str, str]:
        if history:
            history_block = "\n".join(f"• {t}" for t in history[-100:])
        else:
            history_block = "(none — this is the first run)"

        prompt = USER_TEMPLATE.format(
            date=datetime.now().strftime("%B %d, %Y"),
            history_block=history_block,
        )
        return SYSTEM, prompt
