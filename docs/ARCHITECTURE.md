# 🏗️ Architecture Deep-Dive

## Overview

This document walks through the **why** behind each design decision in the AI Research Agent.

---

## 1. Why a Multi-Agent Pipeline?

A naive approach would be to dump every Tavily result into a single LLM call with the prompt *"write a report"*. This fails because:

- 🛑 **Context overload** — 7 searches × 5 results × 700 chars ≈ 24k tokens of noisy evidence
- 🛑 **Schema drift** — single-prompt outputs are inconsistent between runs
- 🛑 **No specialization** — analysis, strategy, and copywriting need very different system prompts

Instead, we split the work into 4 specialized agents, each with:
- A **narrow system prompt** (single role)
- A **strict JSON output schema** where structure matters
- A **focused evidence subset** (only the searches relevant to its job)

```
Research → Analyze (facts) → Strategize (insights) → Pitch (persuasion)
```

This mirrors how a real consulting firm produces a deliverable:
**Junior analyst gathers → Senior analyst structures → Strategist synthesizes → Partner pitches.**

---

## 2. Evidence Layer (Tavily)

We chose Tavily over SerpAPI / DuckDuckGo because:

| Dimension | Tavily | SerpAPI | DuckDuckGo |
|---|---|---|---|
| Designed for agents | ✅ | ❌ | ❌ |
| Returns clean snippets | ✅ | ⚠️ Raw HTML | ⚠️ |
| Includes synthesized `answer` | ✅ | ❌ | ❌ |
| Free tier | 1000/mo | 100/mo | Unlimited but low quality |

We run **7 parallel topical searches** (overview, leadership, news, products, challenges, financials, competitors) rather than one broad search — this gives each downstream agent a curated slice.

---

## 3. JSON Mode & Schema Enforcement

Groq's Llama 3.3 supports `response_format={"type": "json_object"}`. We use this for the Analyst and Strategist agents to guarantee parseable output.

But we still defensive-parse:

```python
def _safe_json(raw):
    raw = strip_markdown_fences(raw)
    try: return json.loads(raw)
    except: return json.loads(regex_find_braces(raw))
```

This handles three failure modes seen in practice:
1. Model wraps JSON in ` ```json ... ``` `
2. Model includes a preamble like *"Here is the JSON:"*
3. Model emits malformed JSON (trailing commas)

---

## 4. Hallucination Guardrails

Hallucinated leadership names are the #1 risk in a tool like this. We mitigate via:

1. **Evidence-first prompting** — Analyst is told: *"Use real names ONLY from the evidence. Never invent a person."*
2. **Empty-array escape** — *"If none found, return an empty array."* — turns hallucination into a graceful "no data" state.
3. **Targeted leadership search** — a dedicated Tavily query for `{company} CEO CTO founder director leadership team` increases recall.
4. **UI honesty** — when `leaders` is empty, the UI explicitly says so rather than rendering placeholder cards.

For generic AI suggestions, the Strategist's prompt includes a **few-shot specificity example**:
> *Examples of GOOD specificity: "AI-powered floor-plan vectorization for Adani Realty's brochure pipeline" — not "use AI for documents".*

This single sentence dramatically improves output quality.

---

## 5. Why Groq?

| Provider | Llama 3.3 70B latency | Cost (free tier) |
|---|---|---|
| Groq | **~0.8s / 1k tokens** | 14,400 req/day |
| OpenAI GPT-4o | ~3s / 1k tokens | $5 trial credit |
| Together AI | ~2s / 1k tokens | $1 trial credit |

Groq's LPU inference is roughly **3–5× faster** than commodity GPU stacks. End-to-end report generation is **30–50 seconds**, mostly Tavily I/O — actual LLM time is under 8 seconds across all 4 agents.

The smaller **Llama 3.1 8B Instant** is used for chat follow-ups because:
- Context is already curated (the report itself)
- Answers should feel real-time (<300ms)

---

## 6. UI Design Decisions

| Choice | Reasoning |
|---|---|
| Streamlit (not Next.js) | 10× faster to ship; built-in chat, downloads, file uploads |
| Dark gradient theme | Premium feel; reduces eye strain in demo settings |
| Tab navigation | 6 report sections fit naturally as tabs — better than scrolling |
| Initials-based avatars | Avoid LinkedIn TOS issues from scraping profile photos |
| Chat as a tab | Encourages report-grounded Q&A rather than free-form |

---

## 7. Export Pipeline

`exporter.to_markdown()` and `exporter.to_pdf()` consume the **same canonical report dict**. This guarantees that all three artifacts (UI, MD, PDF) stay in sync.

ReportLab Platypus is used because:
- Pure Python (no Chrome/Playwright headless dependency)
- Pixel-stable across platforms
- Fast (<200ms for a 5-page report)

---

## 8. Future Architecture

If we needed to scale this beyond a demo:

```
                ┌──────────────────────────────────────────┐
                │           API Gateway (FastAPI)          │
                └────────────────────┬─────────────────────┘
                                     │
        ┌────────────────────────────┼────────────────────────────┐
        ▼                            ▼                            ▼
  ┌──────────┐              ┌──────────────────┐         ┌────────────────┐
  │ Redis    │              │ Celery worker    │         │  Postgres      │
  │ (cache)  │◀────────────▶│  (4 agents in    │◀───────▶│  (reports DB)  │
  └──────────┘              │   parallel)      │         └────────────────┘
                            └──────────────────┘
                                     │
                          ┌──────────┴───────────┐
                          ▼                      ▼
                     ┌──────────┐         ┌─────────────┐
                     │  Groq    │         │   Tavily    │
                     └──────────┘         └─────────────┘
```

- **Redis cache** keyed by `company_name` (24h TTL) — avoid re-running for popular companies
- **Celery / RQ** for async background generation + email delivery
- **Postgres** for report history, user accounts, sharing
- **LangGraph** for richer agent loops (e.g. "if leadership empty, retry with deeper search")
