"""Base class for AI observer agents."""
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import anthropic

ROOT = Path(__file__).parent.parent

ICON_MAP = {
    # Market
    "funding": "attach_money",
    "ipo": "show_chart",
    "regulation": "gavel",
    "forecast": "trending_up",
    "enterprise": "business",
    "m_a": "merge_type",
    "partnership": "handshake",
    "revenue": "bar_chart",
    "market_share": "pie_chart",
    # Tech
    "new_model": "smart_toy",
    "breakthrough": "rocket_launch",
    "big_tech": "corporate_fare",
    "research": "science",
    "product": "devices",
    "infrastructure": "cloud",
    "open_source": "code",
    "acquisition": "merge_type",
}


class BaseObserver:
    section_id: str = ""
    history_filename: str = ""

    def __init__(self):
        self.data_dir = ROOT / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.html_file = ROOT / "index.html"
        self.client = anthropic.Anthropic()

    # ── History ──────────────────────────────────────────────────────────────

    def load_history(self) -> list[str]:
        path = self.data_dir / self.history_filename
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8")).get("topics", [])
        return []

    def save_history(self, new_topics: list[str]) -> None:
        path = self.data_dir / self.history_filename
        existing = self.load_history()
        merged = (existing + new_topics)[-300:]  # keep last 300 titles
        path.write_text(
            json.dumps({"topics": merged, "updated": datetime.now().isoformat()},
                       ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    # ── Claude call ──────────────────────────────────────────────────────────

    def call_claude(self, system: str, prompt: str) -> str:
        """Call Claude with web search. Returns concatenated text blocks."""
        messages = [{"role": "user", "content": prompt}]
        tools = [{"type": "web_search_20250305", "name": "web_search"}]

        # Agentic loop — handle server-side tool use
        for iteration in range(10):
            try:
                response = self.client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=8192,
                    system=system,
                    tools=tools,
                    messages=messages,
                )
            except (anthropic.BadRequestError, anthropic.APIStatusError) as exc:
                print(f"  Web search unavailable ({exc}), retrying without it…")
                response = self.client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=8192,
                    system=system,
                    messages=messages,
                )

            texts = [b.text for b in response.content if getattr(b, "type", None) == "text"]

            if response.stop_reason == "end_turn":
                return "\n".join(texts)

            if response.stop_reason == "tool_use":
                # Add assistant turn and provide tool results to continue
                messages.append({"role": "assistant", "content": response.content})
                tool_results = [
                    {
                        "type": "tool_result",
                        "tool_use_id": b.id,
                        "content": "Search executed by server.",
                    }
                    for b in response.content
                    if getattr(b, "type", None) == "tool_use"
                ]
                if tool_results:
                    messages.append({"role": "user", "content": tool_results})
                continue

            # max_tokens or unexpected stop — return what we have
            return "\n".join(texts)

        return ""

    # ── JSON extraction ───────────────────────────────────────────────────────

    def parse_items(self, raw: str) -> list[dict]:
        # 1) fenced code block
        m = re.search(r"```(?:json)?\s*(\[[\s\S]*?\])\s*```", raw)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
        # 2) bare JSON array (greedy last match)
        for match in re.finditer(r"\[[\s\S]*?\]", raw):
            try:
                data = json.loads(match.group())
                if data and isinstance(data[0], dict):
                    return data
            except json.JSONDecodeError:
                pass
        return []

    # ── HTML generation ───────────────────────────────────────────────────────

    def _badge_class(self, category: str) -> str:
        return "b-" + category.lower().replace(" ", "_").replace("-", "_")

    def generate_review_block(self, items: list[dict]) -> str:
        now = datetime.now()
        date_str = now.strftime("%d %B %Y • %H:%M")

        rows = []
        for item in items:
            cat   = item.get("category", "general").lower().replace(" ", "_").replace("-", "_")
            imp   = item.get("importance", "medium")
            title = item.get("title", "").replace("<", "&lt;").replace(">", "&gt;")
            body  = item.get("details", "").replace("<", "&lt;").replace(">", "&gt;")
            icon  = ICON_MAP.get(cat, "info")
            badge = self._badge_class(cat)
            label = cat.replace("_", " ").title()

            rows.append(
                f'        <div class="acc-item imp-{imp}">\n'
                f'            <button class="acc-btn" onclick="toggleAccordion(this)">\n'
                f'                <span class="material-icons acc-icon">{icon}</span>\n'
                f'                <span class="acc-title">{title}</span>\n'
                f'                <span class="badge {badge}">{label}</span>\n'
                f'                <span class="material-icons chevron">expand_more</span>\n'
                f'            </button>\n'
                f'            <div class="acc-body"><p>{body}</p></div>\n'
                f'        </div>'
            )

        items_html = "\n".join(rows)
        return (
            f'    <div class="review-block" data-date="{now.isoformat()}">\n'
            f'        <div class="review-meta">\n'
            f'            <span class="material-icons">update</span>\n'
            f'            <span class="review-date">{date_str}</span>\n'
            f'            <span class="review-count">{len(items)} insights</span>\n'
            f'        </div>\n'
            f'        <div class="accordion">\n'
            f'{items_html}\n'
            f'        </div>\n'
            f'    </div>'
        )

    # ── HTML update ───────────────────────────────────────────────────────────

    def update_html(self, new_block: str) -> None:
        content = self.html_file.read_text(encoding="utf-8")
        start = f"<!-- {self.section_id.upper()}_START -->"
        end   = f"<!-- {self.section_id.upper()}_END -->"

        pattern = re.compile(
            re.escape(start) + r"([\s\S]*?)" + re.escape(end)
        )
        m = pattern.search(content)
        if not m:
            raise ValueError(f"Marker {start} not found in index.html")

        inner = m.group(1)
        # Remove empty-state div if present
        inner = re.sub(r"\s*<div class=\"empty-state\">[\s\S]*?</div>", "", inner)
        # Prepend new review block
        new_inner = f"\n{new_block}\n{inner}"

        new_content = content[: m.start(1)] + new_inner + content[m.end(1):]
        self.html_file.write_text(new_content, encoding="utf-8")

    # ── Entry point ───────────────────────────────────────────────────────────

    def run(self) -> None:
        history = self.load_history()
        system, prompt = self.build_prompts(history)

        print(f"[{self.section_id.upper()}] Calling Claude with web search…")
        raw = self.call_claude(system, prompt)

        if not raw:
            print("ERROR: empty response from Claude", file=sys.stderr)
            sys.exit(1)

        items = self.parse_items(raw)
        if not items:
            print("ERROR: could not parse JSON items. Raw output:", file=sys.stderr)
            print(raw[:800], file=sys.stderr)
            sys.exit(1)

        items = items[:20]
        print(f"  Parsed {len(items)} items")

        block = self.generate_review_block(items)
        self.update_html(block)

        self.save_history([i.get("title", "") for i in items])
        print(f"  ✓ {self.section_id.upper()} section updated in index.html")

    def build_prompts(self, history: list[str]) -> tuple[str, str]:
        raise NotImplementedError
