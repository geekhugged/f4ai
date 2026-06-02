"""Glossary Observer — 100 key AI/ML terms with Russian definitions."""
from .base_observer import BaseObserver
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent

SYSTEM = """You are an AI Education Agent. Compile a comprehensive, accessible glossary \
of the 100 most important terms in artificial intelligence and machine learning.

Cover all 8 categories evenly (~12-13 terms each):
• basics       — token, model, parameter, neural network, weight, bias, inference, training
• architecture — transformer, attention, embedding, layer, MoE, positional encoding, residual
• training     — pre-training, fine-tuning, RLHF, backpropagation, gradient descent, LoRA, SFT
• inference    — context window, temperature, sampling, KV-cache, quantization, latency, throughput
• capabilities — reasoning, chain-of-thought, multimodal, RAG, in-context learning, benchmark, CoT
• safety       — hallucination, alignment, red teaming, guardrails, jailbreak, constitutional AI
• agents       — agent, tool use, MCP, function calling, memory, agentic loop, orchestration, ReAct
• business     — prompt engineering, LLMOps, distillation, API, cost-per-token, model serving, SLA

Instructions:
1. Definitions must be in Russian, clear and concrete for a non-technical reader.
2. Use analogies and real examples where helpful.
3. Do NOT search the web — use your existing knowledge.
4. Return ONLY a valid JSON array of exactly 100 objects — nothing else.
   Each object must have:
   - "term"       : English name as used in industry (e.g. "Token", "RAG", "RLHF")
   - "term_ru"    : Russian name or transliteration (e.g. "Токен", "RAG / Поиск с генерацией")
   - "category"   : one of: basics | architecture | training | inference | capabilities | safety | agents | business
   - "definition" : 1-2 sentences in Russian, plain language, max 40 words
"""

USER_TEMPLATE = """\
Generate a glossary of exactly 100 key AI/ML terms in JSON.

Distribute evenly: ~12-13 terms per category (basics, architecture, training, inference, \
capabilities, safety, agents, business). Start with the most fundamental (Token, Neural Network, \
Parameter) and include advanced concepts (MoE, Constitutional AI, Agentic Loop, LoRA).

Return ONLY the JSON array of exactly 100 objects. No markdown, no extra text."""

CAT_LABELS = {
    "basics":       "Основы",
    "architecture": "Архитектура",
    "training":     "Обучение",
    "inference":    "Инференс",
    "capabilities": "Возможности",
    "safety":       "Безопасность",
    "agents":       "Агенты",
    "business":     "Технологии",
}

CAT_ICONS = {
    "basics":       "school",
    "architecture": "account_tree",
    "training":     "fitness_center",
    "inference":    "speed",
    "capabilities": "psychology",
    "safety":       "shield",
    "agents":       "smart_toy",
    "business":     "settings",
}


class GlossaryObserver(BaseObserver):
    section_id = "glossary"

    def _catalogue_path(self) -> Path:
        return ROOT / "data" / "glossary.json"

    def _all_review_files(self) -> list[Path]:
        p = self._catalogue_path()
        return [p] if p.exists() else []

    def load_history(self) -> list[str]:
        return []

    def save_review(self, items: list[dict], review_date: str) -> Path:
        path = self._catalogue_path()
        payload = {
            "section": self.section_id,
            "generated_at": datetime.now().isoformat(),
            "items": items,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def call_claude(self, system: str, prompt: str) -> str:
        """No web search needed; use higher token limit for 100 items."""
        import anthropic
        messages = [{"role": "user", "content": prompt}]

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=16000,
                system=system,
                messages=messages,
            )
        except anthropic.BadRequestError:
            # Fallback to 8192 if model doesn't support 16k
            try:
                response = self.client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=8192,
                    system=system,
                    messages=messages,
                )
            except anthropic.APIStatusError as exc:
                print(f"  API error: {exc}", file=sys.stderr)
                return ""

        texts = [b.text for b in response.content if getattr(b, "type", None) == "text"]
        result = "\n".join(texts)
        if not result:
            print(f"  Warning: empty text, stop_reason={response.stop_reason}", file=sys.stderr)
        return result

    def parse_items(self, raw: str) -> list[dict]:
        """Find the largest JSON array whose items have a 'term' key."""
        candidates = []
        fb = re.search(r"```(?:json)?\s*(\[[\s\S]*?\])\s*```", raw)
        if fb:
            try:
                data = json.loads(fb.group(1))
                if data and isinstance(data[0], dict) and "term" in data[0]:
                    candidates.append(data)
            except json.JSONDecodeError:
                pass
        for m in re.finditer(r"\[[\s\S]*?\]", raw):
            try:
                data = json.loads(m.group())
                if data and isinstance(data[0], dict) and "term" in data[0]:
                    candidates.append(data)
            except json.JSONDecodeError:
                pass
        return max(candidates, key=len) if candidates else []

    def _glossary_html(self, items: list[dict]) -> str:
        rows = []
        for item in items:
            term    = item.get("term", "").replace("<", "&lt;").replace(">", "&gt;")
            term_ru = item.get("term_ru", term).replace("<", "&lt;").replace(">", "&gt;")
            cat     = item.get("category", "basics").lower()
            defn    = item.get("definition", "").replace("<", "&lt;").replace(">", "&gt;")
            icon    = CAT_ICONS.get(cat, "info")
            label   = CAT_LABELS.get(cat, cat.title())
            search  = f"{term.lower()} {term_ru.lower()}"

            rows.append(
                f'        <div class="acc-item gl-item" data-cat="{cat}" data-term="{search}">\n'
                f'            <button class="acc-btn" onclick="toggleAccordion(this)">\n'
                f'                <span class="material-icons acc-icon">{icon}</span>\n'
                f'                <span class="gl-term-name">{term_ru}'
                f'<small>{term}</small></span>\n'
                f'                <span class="badge b-gl-{cat}">{label}</span>\n'
                f'                <span class="material-icons chevron">expand_more</span>\n'
                f'            </button>\n'
                f'            <div class="acc-body"><p>{defn}</p>\n'
                f'            </div>\n'
                f'        </div>'
            )

        items_html = "\n".join(rows)
        return (
            f'\n    <div class="review-block">\n'
            f'        <div class="accordion" id="glossaryAccordion">\n'
            f'{items_html}\n'
            f'        </div>\n'
            f'    </div>\n        '
        )

    def rebuild_html_section(self) -> None:
        path = self._catalogue_path()
        if not path.exists():
            new_inner = (
                '\n        <div class="empty-state">'
                '<span class="material-icons">school</span>'
                '<h3>Глоссарий ещё не сгенерирован</h3>'
                '<p>Запустите <code>python run_observers.py --glossary</code></p>'
                '</div>\n        '
            )
        else:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                new_inner = self._glossary_html(data["items"])
            except (json.JSONDecodeError, KeyError) as exc:
                print(f"  Warning: could not read glossary ({exc})", file=sys.stderr)
                return

        content = self.html_file.read_text(encoding="utf-8")
        start   = "<!-- GLOSSARY_START -->"
        end     = "<!-- GLOSSARY_END -->"
        pattern = re.compile(re.escape(start) + r"[\s\S]*?" + re.escape(end))
        if not pattern.search(content):
            raise ValueError("GLOSSARY markers not found in index.html")
        new_content = pattern.sub(f"{start}{new_inner}{end}", content)
        self.html_file.write_text(new_content, encoding="utf-8")

    def build_prompts(self, history: list[str], review_date: str) -> tuple[str, str]:
        return SYSTEM, USER_TEMPLATE

    def run(self, review_date: str) -> None:
        system, prompt = self.build_prompts([], review_date)
        print("[GLOSSARY] Generating AI glossary (100 terms)…")
        raw = self.call_claude(system, prompt)

        if not raw:
            print("ERROR: empty response from Claude", file=sys.stderr)
            sys.exit(1)

        items = self.parse_items(raw)
        if not items:
            print("ERROR: could not parse JSON. Raw output:", file=sys.stderr)
            print(raw[:800], file=sys.stderr)
            sys.exit(1)

        items = items[:100]
        saved = self.save_review(items, review_date)
        print(f"  Saved {len(items)} terms → {saved.relative_to(ROOT)}")
        self.rebuild_html_section()
        print("  ✓ index.html updated (glossary section rebuilt)")
