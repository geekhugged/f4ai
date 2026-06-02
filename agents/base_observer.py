"""Base class for AI observer agents."""
import json
import os
import re
import sys
from datetime import date as DateType, datetime
from pathlib import Path

import anthropic

ROOT = Path(__file__).parent.parent


def _make_client() -> anthropic.Anthropic:
    """Create Anthropic client: ANTHROPIC_API_KEY → session token → error."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        return anthropic.Anthropic(api_key=api_key)
    token_file = os.environ.get("CLAUDE_SESSION_INGRESS_TOKEN_FILE")
    if token_file and Path(token_file).exists():
        return anthropic.Anthropic(auth_token=Path(token_file).read_text().strip())
    raise RuntimeError(
        "No auth found. Set ANTHROPIC_API_KEY or run inside a Claude Code session."
    )

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
    # Startup
    "launch": "bolt",
    "founder": "person",
    "accelerator": "school",
    "unicorn": "star",
    "pivot": "sync_alt",
    # Forecast / Future of work
    "high_risk":      "warning",
    "medium_risk":    "trending_down",
    "low_risk":       "verified",
    "new_roles":      "add_circle",
    "transformation": "autorenew",
    "timeline":       "schedule",
    "strategy":       "lightbulb",
    "society":        "groups",
}

EMPTY_STATES = {
    "market": (
        '<div class="empty-state">'
        '<span class="material-icons">show_chart</span>'
        '<h3>Обзоров пока нет</h3>'
        '<p>Запустите <code>python run_observers.py --market</code></p>'
        '</div>'
    ),
    "tech": (
        '<div class="empty-state">'
        '<span class="material-icons">rocket_launch</span>'
        '<h3>Обзоров пока нет</h3>'
        '<p>Запустите <code>python run_observers.py --tech</code></p>'
        '</div>'
    ),
    "startup": (
        '<div class="empty-state">'
        '<span class="material-icons">bolt</span>'
        '<h3>Обзоров пока нет</h3>'
        '<p>Запустите <code>python run_observers.py --startup</code></p>'
        '</div>'
    ),
    "llm": (
        '<div class="empty-state">'
        '<span class="material-icons">smart_toy</span>'
        '<h3>Каталог ещё не сгенерирован</h3>'
        '<p>Запустите <code>python run_observers.py --llm</code></p>'
        '</div>'
    ),
    "forecast": (
        '<div class="empty-state">'
        '<span class="material-icons">work_history</span>'
        '<h3>Обзоров пока нет</h3>'
        '<p>Запустите <code>python run_observers.py --forecast</code></p>'
        '</div>'
    ),
}


class BaseObserver:
    section_id: str = ""

    def __init__(self):
        self.data_dir = ROOT / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.html_file = ROOT / "index.html"
        self.client = _make_client()

    # ── Review file helpers ───────────────────────────────────────────────────

    def _review_path(self, review_date: str) -> Path:
        """Returns path like data/market_2026-06-02.json."""
        return self.data_dir / f"{self.section_id}_{review_date}.json"

    def _all_review_files(self) -> list[Path]:
        """All review JSON files for this section, sorted newest-first."""
        return sorted(
            self.data_dir.glob(f"{self.section_id}_*.json"),
            reverse=True,
        )

    # ── History (deduplication) ───────────────────────────────────────────────

    def load_history(self) -> list[str]:
        """Collect all previously generated titles from data files."""
        titles: list[str] = []
        for f in self._all_review_files():
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                titles.extend(item.get("title", "") for item in data.get("items", []))
            except (json.JSONDecodeError, KeyError):
                pass
        return titles[-300:]

    # ── Save review ───────────────────────────────────────────────────────────

    def save_review(self, items: list[dict], review_date: str) -> Path:
        """Write review to data/{section}_{date}.json and return the path."""
        path = self._review_path(review_date)
        payload = {
            "section": self.section_id,
            "review_date": review_date,
            "generated_at": datetime.now().isoformat(),
            "items": items,
        }
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    # ── Claude call ──────────────────────────────────────────────────────────

    def call_claude(self, system: str, prompt: str) -> str:
        """Call Claude with web search. Returns concatenated text blocks."""
        messages = [{"role": "user", "content": prompt}]
        tools = [{"type": "web_search_20250305", "name": "web_search"}]

        for _ in range(10):
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

    # ── JSON extraction ───────────────────────────────────────────────────────

    def parse_items(self, raw: str) -> list[dict]:
        m = re.search(r"```(?:json)?\s*(\[[\s\S]*?\])\s*```", raw)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
        for match in re.finditer(r"\[[\s\S]*?\]", raw):
            try:
                data = json.loads(match.group())
                if data and isinstance(data[0], dict):
                    return data
            except json.JSONDecodeError:
                pass
        return []

    # ── HTML generation ───────────────────────────────────────────────────────

    def _review_block_html(self, items: list[dict], review_date: str, is_open: bool = False) -> str:
        """Build one accordion review block from a list of items."""
        try:
            dt = datetime.strptime(review_date, "%Y-%m-%d")
            date_label = dt.strftime("%d %B %Y")
        except ValueError:
            date_label = review_date

        rows = []
        for item in items:
            cat   = item.get("category", "general").lower().replace(" ", "_").replace("-", "_")
            imp   = item.get("importance", "medium")
            title = item.get("title", "").replace("<", "&lt;").replace(">", "&gt;")
            body  = item.get("details", "").replace("<", "&lt;").replace(">", "&gt;")
            icon  = ICON_MAP.get(cat, "info")
            badge = "b-" + cat
            label = cat.replace("_", " ").title()

            # Build sources HTML
            sources_html = ""
            sources = item.get("sources", [])
            if sources:
                links = []
                for src in sources:
                    src_label = src.get("label", "Source").replace("<", "&lt;").replace(">", "&gt;")
                    src_url   = src.get("url", "#")
                    links.append(
                        f'<a href="{src_url}" target="_blank" rel="noopener noreferrer">'
                        f'<span class="material-icons">open_in_new</span>{src_label}</a>'
                    )
                sources_html = (
                    f'\n            <div class="acc-sources">'
                    f'<span class="sources-label">Sources:</span>'
                    + "".join(links)
                    + f'</div>'
                )

            rows.append(
                f'        <div class="acc-item imp-{imp}">\n'
                f'            <button class="acc-btn" onclick="toggleAccordion(this)">\n'
                f'                <span class="material-icons acc-icon">{icon}</span>\n'
                f'                <span class="acc-title">{title}</span>\n'
                f'                <span class="badge {badge}">{label}</span>\n'
                f'                <span class="material-icons chevron">expand_more</span>\n'
                f'            </button>\n'
                f'            <div class="acc-body"><p>{body}</p>{sources_html}\n'
                f'            </div>\n'
                f'        </div>'
            )

        items_html = "\n".join(rows)
        open_cls = ' open' if is_open else ''
        return (
            f'    <div class="review-block" data-date="{review_date}">\n'
            f'        <button class="review-meta{open_cls}" onclick="toggleReview(this)">\n'
            f'            <span class="material-icons">calendar_today</span>\n'
            f'            <span class="review-date">{date_label}</span>\n'
            f'            <span class="review-count">{len(items)} insights</span>\n'
            f'            <span class="material-icons review-chevron">expand_more</span>\n'
            f'        </button>\n'
            f'        <div class="review-content{open_cls}">\n'
            f'        <div class="accordion">\n'
            f'{items_html}\n'
            f'        </div>\n'
            f'        </div>\n'
            f'    </div>'
        )

    # ── Rebuild HTML section from all JSON files ──────────────────────────────

    def rebuild_html_section(self) -> None:
        """Replace section content in index.html from all data/{section}_*.json."""
        files = self._all_review_files()  # newest first

        if not files:
            new_inner = f"\n        {EMPTY_STATES[self.section_id]}\n        "
        else:
            blocks = []
            for i, f in enumerate(files):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    blocks.append(
                        self._review_block_html(data["items"], data["review_date"], is_open=(i == 0))
                    )
                except (json.JSONDecodeError, KeyError) as exc:
                    print(f"  Warning: skipping {f.name} ({exc})", file=sys.stderr)
            new_inner = "\n" + "\n".join(blocks) + "\n        "

        content = self.html_file.read_text(encoding="utf-8")
        start = f"<!-- {self.section_id.upper()}_START -->"
        end   = f"<!-- {self.section_id.upper()}_END -->"
        pattern = re.compile(re.escape(start) + r"[\s\S]*?" + re.escape(end))

        if not pattern.search(content):
            raise ValueError(f"Marker {start} not found in index.html")

        new_content = pattern.sub(f"{start}{new_inner}{end}", content)
        self.html_file.write_text(new_content, encoding="utf-8")

    # ── Entry point ───────────────────────────────────────────────────────────

    def run(self, review_date: str) -> None:
        """Generate a review for review_date (YYYY-MM-DD) and write to file."""
        out_path = self._review_path(review_date)
        if out_path.exists():
            print(f"  Review for {review_date} already exists: {out_path.name}")
            print("  Delete the file and re-run to regenerate.")
            self.rebuild_html_section()
            return

        history = self.load_history()
        system, prompt = self.build_prompts(history, review_date)

        print(f"[{self.section_id.upper()}] Generating review for {review_date}…")
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
        saved = self.save_review(items, review_date)
        print(f"  Saved {len(items)} items → {saved.relative_to(ROOT)}")

        self.rebuild_html_section()
        print(f"  ✓ index.html updated ({self.section_id} section rebuilt)")

    def build_prompts(self, history: list[str], review_date: str) -> tuple[str, str]:
        raise NotImplementedError
