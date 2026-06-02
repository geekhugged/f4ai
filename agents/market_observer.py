"""Market Observer — AI market trends, funding, regulation, forecasts."""
from datetime import datetime
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
1. Search the web for AI market news from the last 7–14 days.
2. Prioritise specific numbers, company names, dates, and dollar amounts.
3. Return ONLY a valid JSON array of exactly 20 objects — nothing else.
   Each object must have:
   - "title"      : concise headline, max 15 words
   - "details"    : 2-3 sentences with concrete facts and figures
   - "category"   : one of: funding | ipo | regulation | forecast | enterprise | m_a | partnership | revenue | market_share
   - "importance" : "high" | "medium" | "low"
"""

USER_TEMPLATE = """\
Today is {date}.

Search for the latest AI market news and return 20 NEW, UNIQUE insights.

PREVIOUSLY COVERED TOPICS — do NOT repeat any of these:
{history_block}

Generate 20 fresh market insights that differ from everything above.
Return ONLY the JSON array. No markdown, no explanation text."""


class MarketObserver(BaseObserver):
    section_id = "market"
    history_filename = "market_history.json"

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
