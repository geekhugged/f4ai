"""LLM Observer — chronological catalogue of major AI models from Big Tech."""
from .base_observer import BaseObserver
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

SYSTEM = """You are an AI Model Catalogue agent. Your job is to compile an accurate, \
comprehensive chronological catalogue of the most important large language models \
and AI models released by major companies.

Cover models from: OpenAI, Anthropic, Google (DeepMind), Meta, Microsoft, Mistral, \
xAI (Grok), Alibaba (Qwen), Baidu (ERNIE), Cohere, Amazon, Apple, Samsung, and \
other significant AI labs.

Instructions:
1. Search the web to verify release dates and model details.
2. List models in chronological order by release date (oldest first).
3. Include only publicly released or announced models — no speculation.
4. Return ONLY a valid JSON array of exactly 50 objects — nothing else.
   Each object must have:
   - "name"        : model name including version (e.g. "GPT-4o", "Claude 3.5 Sonnet")
   - "company"     : company/lab name
   - "released"    : release date or year as string (e.g. "2024-05", "2023")
   - "category"    : one of: llm | multimodal | reasoning | image | audio | video | code | embedding
   - "description" : 1 sentence — key capability, context window, or notable first (max 25 words)
   - "sources"     : array of 1-2 objects, each with "label" and "url"
"""

USER_TEMPLATE = """\
Compile a chronological catalogue of the 50 most important AI models from Big Tech companies.

Focus on models released up to {cutoff_date}. Order by release date, oldest first.
Include flagship models and notable releases — prioritise variety across companies.

Return ONLY the JSON array of exactly 50 objects. No markdown, no extra text."""


class LlmObserver(BaseObserver):
    section_id = "llm"

    # LLM catalogue stores a single file (not date-partitioned)
    def _catalogue_path(self) -> Path:
        return ROOT / "data" / "llm_catalogue.json"

    def load_history(self) -> list[str]:
        return []  # catalogue is always regenerated fresh

    def save_review(self, items: list[dict], review_date: str) -> Path:
        path = self._catalogue_path()
        from datetime import datetime
        payload = {
            "section": self.section_id,
            "review_date": review_date,
            "generated_at": datetime.now().isoformat(),
            "items": items,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def _all_review_files(self) -> list[Path]:
        p = self._catalogue_path()
        return [p] if p.exists() else []

    def _review_block_html(self, items: list[dict], review_date: str, is_open: bool = False) -> str:
        from datetime import datetime
        try:
            dt = datetime.strptime(review_date, "%Y-%m-%d")
            date_label = dt.strftime("%d %B %Y")
        except ValueError:
            date_label = review_date

        COMPANY_COLORS = {
            "openai":     ("#e8f0fe", "#1a73e8"),
            "anthropic":  ("#fce8e6", "#d93025"),
            "google":     ("#e6f4ea", "#1e8e3e"),
            "deepmind":   ("#e6f4ea", "#1e8e3e"),
            "meta":       ("#e8f0fe", "#1a73e8"),
            "microsoft":  ("#e0f7fa", "#0097a7"),
            "mistral":    ("#f3e8fd", "#9334e6"),
            "xai":        ("#fff3e0", "#e65100"),
            "alibaba":    ("#fce4ec", "#c62828"),
            "baidu":      ("#fff8e1", "#f57f17"),
            "cohere":     ("#e8f5e9", "#2e7d32"),
            "amazon":     ("#fff8e1", "#e37400"),
            "apple":      ("#f3e8fd", "#7b1fa2"),
        }

        CAT_ICONS = {
            "llm":        "chat",
            "multimodal": "image",
            "reasoning":  "psychology",
            "image":      "photo",
            "audio":      "headphones",
            "video":      "movie",
            "code":       "code",
            "embedding":  "hub",
        }

        rows = []
        for item in items:
            name    = item.get("name", "").replace("<", "&lt;").replace(">", "&gt;")
            company = item.get("company", "").replace("<", "&lt;").replace(">", "&gt;")
            released= item.get("released", "").replace("<", "&lt;").replace(">", "&gt;")
            cat     = item.get("category", "llm").lower()
            desc    = item.get("description", "").replace("<", "&lt;").replace(">", "&gt;")
            imp     = item.get("importance", "medium")
            icon    = CAT_ICONS.get(cat, "smart_toy")

            co_key = company.lower().split()[0] if company.split() else ""
            bg, fg = COMPANY_COLORS.get(co_key, ("#f1f3f4", "#5f6368"))
            co_badge = (
                f'<span class="badge" style="background:{bg};color:{fg};">{company}</span>'
            )
            cat_badge = (
                f'<span class="badge b-llm-{cat}">{cat}</span>'
            )

            sources_html = ""
            for src in item.get("sources", []):
                src_label = src.get("label", "Source").replace("<", "&lt;").replace(">", "&gt;")
                src_url   = src.get("url", "#")
                sources_html += (
                    f'<a href="{src_url}" target="_blank" rel="noopener noreferrer">'
                    f'<span class="material-icons">open_in_new</span>{src_label}</a>'
                )
            if sources_html:
                sources_html = (
                    f'\n            <div class="acc-sources">'
                    f'<span class="sources-label">Sources:</span>{sources_html}</div>'
                )

            rows.append(
                f'        <div class="acc-item imp-medium llm-entry">\n'
                f'            <button class="acc-btn" onclick="toggleAccordion(this)">\n'
                f'                <span class="material-icons acc-icon">{icon}</span>\n'
                f'                <span class="acc-title">'
                f'<strong>{name}</strong>'
                f'<span class="llm-date">{released}</span>'
                f'</span>\n'
                f'                {co_badge}\n'
                f'                {cat_badge}\n'
                f'                <span class="material-icons chevron">expand_more</span>\n'
                f'            </button>\n'
                f'            <div class="acc-body"><p>{desc}</p>{sources_html}\n'
                f'            </div>\n'
                f'        </div>'
            )

        items_html = "\n".join(rows)
        open_cls = ' open' if is_open else ''
        return (
            f'    <div class="review-block" data-date="{review_date}">\n'
            f'        <button class="review-meta{open_cls}" onclick="toggleReview(this)">\n'
            f'            <span class="material-icons">calendar_today</span>\n'
            f'            <span class="review-date">Обновлено: {date_label}</span>\n'
            f'            <span class="review-count">{len(items)} моделей</span>\n'
            f'            <span class="material-icons review-chevron">expand_more</span>\n'
            f'        </button>\n'
            f'        <div class="review-content{open_cls}">\n'
            f'        <div class="accordion">\n'
            f'{items_html}\n'
            f'        </div>\n'
            f'        </div>\n'
            f'    </div>'
        )

    def parse_items(self, raw: str) -> list[dict]:
        """Find the largest JSON array whose first element has a 'name' key."""
        import re, json
        candidates = []
        for m in re.finditer(r"\[[\s\S]*?\]", raw):
            try:
                data = json.loads(m.group())
                if data and isinstance(data[0], dict) and "name" in data[0]:
                    candidates.append(data)
            except json.JSONDecodeError:
                pass
        # also try fenced block
        fb = re.search(r"```(?:json)?\s*(\[[\s\S]*?\])\s*```", raw)
        if fb:
            try:
                data = json.loads(fb.group(1))
                if data and isinstance(data[0], dict) and "name" in data[0]:
                    candidates.append(data)
            except json.JSONDecodeError:
                pass
        if not candidates:
            return []
        return max(candidates, key=len)

    def call_claude(self, system: str, prompt: str) -> str:
        """Override to use higher token limit for the large catalogue."""
        import anthropic
        messages = [{"role": "user", "content": prompt}]
        tools = [{"type": "web_search_20250305", "name": "web_search"}]

        for _ in range(10):
            try:
                response = self.client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=16000,
                    system=system,
                    tools=tools,
                    messages=messages,
                )
            except (anthropic.BadRequestError, anthropic.APIStatusError):
                response = self.client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=16000,
                    system=system,
                    messages=messages,
                )

            texts = [b.text for b in response.content if getattr(b, "type", None) == "text"]

            if response.stop_reason == "end_turn":
                return "\n".join(texts)

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results = [
                    {"type": "tool_result", "tool_use_id": b.id, "content": "Search executed."}
                    for b in response.content
                    if getattr(b, "type", None) == "tool_use"
                ]
                if tool_results:
                    messages.append({"role": "user", "content": tool_results})
                continue

            return "\n".join(texts)

        return ""

    def build_prompts(self, history: list[str], review_date: str) -> tuple[str, str]:
        return SYSTEM, USER_TEMPLATE.format(cutoff_date=review_date)

    def run(self, review_date: str) -> None:
        history = []
        system, prompt = self.build_prompts(history, review_date)

        print(f"[LLM] Generating model catalogue for {review_date}…")
        raw = self.call_claude(system, prompt)

        if not raw:
            print("ERROR: empty response from Claude", file=sys.stderr)
            sys.exit(1)

        items = self.parse_items(raw)
        if not items:
            print("ERROR: could not parse JSON items. Raw output:", file=sys.stderr)
            print(raw[:800], file=sys.stderr)
            sys.exit(1)

        items = items[:50]
        saved = self.save_review(items, review_date)
        print(f"  Saved {len(items)} models → {saved.relative_to(ROOT)}")

        self.rebuild_html_section()
        print(f"  ✓ index.html updated (llm section rebuilt)")
