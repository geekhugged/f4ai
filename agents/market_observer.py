"""Market Observer — AI market trends, funding, regulation, forecasts."""
from .base_observer import BaseObserver

SYSTEM = """You are an AI Market Observer agent. Your job is to produce a factual, \
data-rich summary of the most recent developments in the artificial intelligence market.

Cover:
• Funding rounds, valuations, venture capital activity
• IPOs, M&A deals, acquisitions
• Market share dynamics and competitive landscape
• Revenue reports and financial results
• Regulatory actions, government policy, antitrust
• Enterprise AI adoption and procurement trends
• Analyst market-size forecasts and revised outlooks
• Strategic partnerships and joint ventures

Instructions:
1. Search the web for AI market news around the review date.
2. Prioritise specific numbers, company names, dates, and dollar amounts.
3. Return ONLY a valid JSON array of exactly 20 objects — nothing else.
   Each object must have:
   - "title"      : concise headline, max 15 words
   - "details"    : 2-3 sentences with concrete facts and figures
   - "category"   : one of: funding | ipo | regulation | forecast | enterprise | m_a | partnership | revenue | market_share
   - "importance" : "high" | "medium" | "low"
   - "sources"    : array of 1-3 objects, each with "label" (publication name) and "url" (direct link to article)
"""

USER_TEMPLATE = """\
Review date: {review_date}

Search for AI market news around this date and return 20 NEW, UNIQUE insights.

PREVIOUSLY COVERED TOPICS — do NOT repeat any of these:
{history_block}

Generate 20 fresh market insights not listed above.
Return ONLY the JSON array. No markdown, no extra text."""


class MarketObserver(BaseObserver):
    section_id = "market"

    def build_prompts(self, history: list[str], review_date: str) -> tuple[str, str]:
        history_block = (
            "\n".join(f"• {t}" for t in history[-100:])
            if history else "(none — this is the first run)"
        )
        return SYSTEM, USER_TEMPLATE.format(
            review_date=review_date,
            history_block=history_block,
        )
