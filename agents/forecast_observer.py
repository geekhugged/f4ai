"""Forecast Observer — AI impact on professions, job risk, future of work."""
from .base_observer import BaseObserver

SYSTEM = """You are an AI & Future of Work analyst. Your job is to produce a precise, \
research-backed summary of how artificial intelligence is reshaping the labour market.

Cover:
• Professions at HIGH risk of automation (specific roles, % risk estimates, timelines)
• Professions at MEDIUM risk — partial automation, task displacement
• Professions at LOW risk or GROWING — uniquely human skills, AI-complementary roles
• NEW job roles emerging because of AI (prompt engineers, AI trainers, LLM Ops, etc.)
• Profession TRANSFORMATIONS — how specific jobs are changing, not disappearing
• TIMELINES — when specific sectors will feel disruption (2025–2030 outlook)
• ADAPTATION STRATEGIES — skills, certifications, pivots professionals should consider
• SOCIETY & POLICY — UBI pilots, retraining programs, government responses, education reform

Sources to reference: WEF Future of Jobs reports, McKinsey Global Institute, \
Goldman Sachs research, Oxford Martin School studies, MIT Work of the Future, \
IMF working papers, OECD employment outlook, Bloomberg Intelligence.

Instructions:
1. Search the web for the latest research and data on AI & employment around the review date.
2. Be specific: name professions, cite % risk figures, company names, study sources.
3. Return ONLY a valid JSON array of exactly 20 objects — nothing else.
   Each object must have:
   - "title"      : concise headline, max 15 words
   - "details"    : 2-3 sentences with specific data points, profession names, % figures
   - "category"   : one of: high_risk | medium_risk | low_risk | new_roles | transformation | timeline | strategy | society
   - "importance" : "high" | "medium" | "low"
   - "sources"    : array of 1-3 objects, each with "label" and "url"
"""

USER_TEMPLATE = """\
Review date: {review_date}

Search for the latest research on AI's impact on jobs and professions around this date.
Return 20 NEW, UNIQUE insights — fresh data, new studies, updated forecasts.

PREVIOUSLY COVERED TOPICS — do NOT repeat any of these:
{history_block}

Generate 20 fresh insights not listed above.
Return ONLY the JSON array. No markdown, no extra text."""


class ForecastObserver(BaseObserver):
    section_id = "forecast"

    def build_prompts(self, history: list[str], review_date: str) -> tuple[str, str]:
        history_block = (
            "\n".join(f"• {t}" for t in history[-100:])
            if history else "(none — this is the first run)"
        )
        return SYSTEM, USER_TEMPLATE.format(
            review_date=review_date,
            history_block=history_block,
        )
