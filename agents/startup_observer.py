"""Startup Observer — hot startup & venture news, launches, founders, accelerators."""
from .base_observer import BaseObserver

SYSTEM = """You are an AI Startup & Venture Observer agent. Your job is to produce a \
precise, up-to-date summary of the hottest startup and venture capital news.

Cover:
• New AI startup launches and product announcements
• Early-stage and growth-stage funding rounds (Series A–C, seed, pre-seed)
• Accelerator cohorts: Y Combinator, a16z, Techstars, etc.
• New unicorn designations and valuation milestones
• Notable founder moves, hires, and departures
• Startup acquisitions and acqui-hires
• Pivots, shutdowns, and notable failures
• Hot trending products (Product Hunt launches, viral demos)
• Solo founder and indie hacker breakouts
• Emerging startup ecosystems and geographies

Instructions:
1. Search the web for startup and venture news around the review date.
2. Focus on startups — avoid mega-rounds ($10B+) and Big Tech covered elsewhere.
3. Be specific: startup names, founders, round sizes, investors, product details.
4. Return ONLY a valid JSON array of exactly 20 objects — nothing else.
   Each object must have:
   - "title"      : concise headline, max 15 words
   - "details"    : 2-3 sentences with concrete facts and figures
   - "category"   : one of: funding | launch | product | founder | acquisition | accelerator | unicorn | pivot
   - "importance" : "high" | "medium" | "low"
   - "sources"    : array of 1-3 objects, each with "label" (publication name) and "url" (direct link to article)
"""

USER_TEMPLATE = """\
Review date: {review_date}

Search for the hottest startup and venture news around this date and return 20 NEW, UNIQUE insights.

PREVIOUSLY COVERED TOPICS — do NOT repeat any of these:
{history_block}

Generate 20 fresh startup & venture insights not listed above.
Return ONLY the JSON array. No markdown, no extra text."""


class StartupObserver(BaseObserver):
    section_id = "startup"

    def build_prompts(self, history: list[str], review_date: str) -> tuple[str, str]:
        history_block = (
            "\n".join(f"• {t}" for t in history[-100:])
            if history else "(none — this is the first run)"
        )
        return SYSTEM, USER_TEMPLATE.format(
            review_date=review_date,
            history_block=history_block,
        )
