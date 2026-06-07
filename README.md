# 🧠 AI-Powered Research & Recommendation Agent

> **An institutional-grade company intelligence platform.** Enter a company name → get a structured report covering business overview, leadership, challenges, AI opportunities, and a personalized CEO pitch — in under a minute.

![Built with](https://img.shields.io/badge/Built%20with-Streamlit-FF4B4B?logo=streamlit)
![LLM](https://img.shields.io/badge/LLM-Groq%20Llama%203.3%2070B-8b5cf6)
![Search](https://img.shields.io/badge/Search-Tavily%20AI-3b82f6)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🌐 **Live web research** | Uses Tavily AI search to gather real-time, citeable evidence |
| 🤖 **Multi-agent pipeline** | Researcher → Analyst → Strategist → Pitch Writer |
| 👥 **Leadership cards** | CEO/CTO/Director profile cards with role & bio |
| ⚠️ **Challenge analysis** | Company-specific business challenges with reasoning |
| 💡 **AI opportunity mapping** | Concrete, non-generic AI use cases per company |
| 🎯 **Personalized CEO pitch** | One-page pitch addressed by name to the CEO |
| 💬 **Chat with the report** | Ask follow-up questions grounded in the report |
| 📕 **PDF & Markdown export** | Download as polished PDF, Markdown, or JSON |
| 🎨 **Dark gradient UI** | Premium look-and-feel, fully responsive |

---

## 🚀 Quick Start

### 1. Clone & install

```bash
git clone <this-repo>
cd ai_research_agent
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Get free API keys (both are free)

| Provider | Sign-up | Why |
|---|---|---|
| **Groq** | https://console.groq.com/keys | LLM inference (Llama 3.3 70B) — blazingly fast |
| **Tavily** | https://app.tavily.com/ | AI-native web search with citations |

### 3. Configure

Either create a `.env` file:

```bash
cp .env.example .env
# edit .env and paste your two keys
```

…or just paste them into the **sidebar** when the app launches.

### 4. Run

```bash
streamlit run app.py
```

Open <http://localhost:8501> and enter a company name (e.g. *Adani Realty*, *Sobha*, *Zomato*).

---

## 🏗️ Architecture

```
                    ┌──────────────────────────────────────────────┐
                    │             Streamlit Frontend               │
                    │   (Dark gradient UI, tabs, profile cards)    │
                    └──────────────────────┬───────────────────────┘
                                           │
                              ┌────────────▼────────────┐
                              │  ResearchOrchestrator   │
                              └────────────┬────────────┘
                                           │
        ┌──────────────┬───────────────────┼───────────────────┬───────────────┐
        ▼              ▼                   ▼                   ▼               ▼
 ┌─────────────┐ ┌──────────────┐  ┌──────────────┐   ┌──────────────┐  ┌──────────┐
 │ Researcher  │ │   Analyst    │  │  Strategist  │   │    Pitch     │  │   Chat   │
 │   Agent     │ │    Agent     │  │    Agent     │   │    Agent     │  │  Agent   │
 │             │ │              │  │              │   │              │  │          │
 │ Tavily ×7   │ │ Llama 3.3    │  │ Llama 3.3    │   │ Llama 3.3    │  │ Llama 8B │
 │ searches    │ │ → JSON       │  │ → JSON       │   │ → Markdown   │  │ grounded │
 └─────────────┘ └──────────────┘  └──────────────┘   └──────────────┘  └──────────┘
        │              │                   │                   │               │
        └──────────────┴───────────────────┴───────────────────┴───────────────┘
                                           │
                              ┌────────────▼────────────┐
                              │     Exporter Module     │
                              │  Markdown · PDF · JSON  │
                              └─────────────────────────┘
```

### Agent responsibilities

1. **ResearcherAgent** — Runs 7 parallel Tavily searches per company:
   `overview · leadership · news · products · challenges · financials · competitors`.
   Returns titled, URL-attributed snippets.

2. **AnalystAgent** — Receives raw evidence, emits **strict JSON**:
   - `overview` (what they do, scale, geography, founded, HQ)
   - `key_business_info` (offerings, developments, expansion, public info)
   - `leadership` (CEO/CTO/founders/directors — real names only)
   - `sources` (URLs actually used)

3. **StrategistAgent** — Connects observed facts to **company-specific** AI use cases:
   - `challenges[]` — title, category, description, reasoning
   - `ai_opportunities[]` — title, problem solved, solution, impact, tech stack

4. **PitchAgent** — Drafts a **one-page personalized pitch** addressed to the CEO by name,
   anchored to the top-3 opportunities. Under 350 words, conversational tone.

5. **ChatAgent** — Lightweight Llama-8B-Instant follow-up Q&A grounded **only** in the
   generated report (RAG-style, single-document context).

### Why this design works

- **Separation of concerns** — each agent has one job and a clear contract (JSON schema).
- **Grounding** — every claim is backed by Tavily evidence; the LLM is instructed to
  say *"Not publicly disclosed"* rather than hallucinate.
- **Robust JSON parsing** — handles markdown fences, partial JSON, and recovery via regex.
- **Specificity guardrails** — the Strategist's system prompt forbids generic advice
  and forces references to observed industry facts.

---

## 🛠️ Tech Stack

| Layer | Choice | Why |
|---|---|---|
| UI | **Streamlit 1.39** | Fastest path to a beautiful demo app |
| LLM | **Groq · Llama 3.3 70B Versatile** | Free tier, <1s latency, strong reasoning |
| Fast LLM (chat) | **Llama 3.1 8B Instant** | Sub-300ms follow-up answers |
| Web search | **Tavily AI** | Built for agents, returns clean summaries + URLs |
| PDF export | **ReportLab 4** | Pixel-perfect, no headless-browser dep |
| Config | **python-dotenv** | Simple key management |

---

## 📂 Project Structure

```
ai_research_agent/
├── app.py                  # Streamlit UI (entry point)
├── agents.py               # Multi-agent pipeline + orchestrator
├── exporter.py             # Markdown + PDF generators
├── requirements.txt
├── .env.example
├── .streamlit/
│   └── config.toml         # Dark theme tokens
├── README.md               # ← you are here
└── docs/
    ├── ARCHITECTURE.md     # Deep-dive architecture
    └── DEMO_SCRIPT.md      # Storyboard for demo video
```

---

## 🧪 Example Run

**Input:** `Adani Realty`

**Output:**
- ✅ 7-search Tavily research bundle (~10s)
- ✅ Structured JSON analyst output (overview + 4 leaders + key info)
- ✅ 5 business challenges with reasoning
- ✅ 5 company-specific AI opportunities (e.g. *"AI-powered floor-plan vectorization for Adani Realty's brochure pipeline"*)
- ✅ 320-word personalized pitch addressed to the CEO by name
- ✅ Downloadable as `.pdf`, `.md`, or `.json`

Total time: **30–50 seconds** on Groq's free tier.

---

## 🔒 Privacy & Safety

- API keys stay in browser session memory; never persisted server-side.
- All LLM prompts include explicit *"do not invent facts"* instructions.
- Leadership names are extracted **only** from retrieved evidence — never hallucinated.
- Source URLs are included in every report for verification.

---

## 🧗 Challenges Encountered (and How They Were Solved)

| Challenge | Solution |
|---|---|
| LLMs sometimes return invalid JSON wrapped in markdown fences | `_safe_json()` strips fences and falls back to regex extraction |
| Generic AI-opportunity outputs ("use a chatbot") | Strategist system prompt explicitly forbids generic advice + few-shot specificity example in prompt |
| Hallucinated leadership names | Researcher emits evidence-only; Analyst is instructed to return `[]` when none found |
| Tavily rate limits | Default plan supports 1000 free queries/month — plenty for demos |
| Long Tavily payloads exceed context | `_format_evidence` enforces a 9000-char budget with per-section truncation |
| PDF rendering of long markdown | ReportLab Platypus + custom paragraph styles + page-break heuristics |

---

## 🎬 Demo Video

A 5–10 minute demo walkthrough should cover:

1. **The problem** (30s) — business teams need pre-meeting intelligence quickly
2. **Live demo** (3–4 min) — run *Adani Realty* end-to-end; show all 6 tabs + chat
3. **Architecture** (1 min) — explain the 4-agent pipeline
4. **AI-tools journey** (1–2 min) — explain why Groq + Tavily + Llama 3.3 + Streamlit
5. **Trade-offs** (1 min) — speed-vs-depth, hallucination guardrails, future work

See [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) for a full storyboard.

---

## 🛣️ Roadmap

- [ ] Cache reports per company in SQLite
- [ ] Add LinkedIn enrichment for leadership cards (via Proxycurl)
- [ ] Multi-language reports
- [ ] Vector-store-backed long-term memory across reports
- [ ] CrewAI / LangGraph migration for richer agent loops

---

## 📜 License

MIT — use, modify, and ship freely.

---

**Built by [Your Name]** · Powered by **Groq Llama 3.3** + **Tavily AI** + **Streamlit**
