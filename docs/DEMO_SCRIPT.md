# 🎬 Demo Video Script (5–10 minutes)

Use this as a teleprompter for your demo recording.
Recommended tool: **Loom** or **OBS Studio**.

---

## ⏱️ Timestamps

| Time | Section | Duration |
|------|---------|----------|
| 00:00 – 00:30 | Introduction & problem | 30s |
| 00:30 – 04:00 | Live demo | 3.5 min |
| 04:00 – 05:30 | Architecture walkthrough | 1.5 min |
| 05:30 – 07:00 | AI tools used & why | 1.5 min |
| 07:00 – 08:30 | Challenges faced + solutions | 1.5 min |
| 08:30 – 09:30 | Future work & wrap-up | 1 min |

---

## 🎙️ Script

### [00:00] Introduction

> "Hi, I'm **[Your Name]**, and I built an **AI-Powered Research & Recommendation Agent** for the intern assessment.
>
> The problem I'm solving: before pitching AI services to a company, you have to do hours of manual research — understand their business, find their pain points, and tailor a pitch. My agent does all of that automatically in under a minute."

---

### [00:30] Live Demo

**[Screen: open browser to http://localhost:8501]**

> "Here's the app. I've already added my Groq and Tavily API keys in the sidebar — both are free tiers.
>
> Let me click *Adani Realty* — one of the example companies from the assessment brief."

**[Click preset, watch progress bar]**

> "Behind the scenes, a **researcher agent** is running 7 parallel web searches via Tavily — for overview, leadership, news, challenges, and more. Then three more agents — analyst, strategist, and pitch writer — process that evidence with Groq's Llama 3.3 70B."

**[Report finishes ~40s]**

> "The report has 6 tabs:
>
> **Overview** — what they do, scale, geographic presence, HQ, founded year.
>
> **Leadership** — actual CEO, CTO, and director names pulled from web evidence, with bios. Notice these are real, verifiable names — the system is explicitly instructed *never* to hallucinate people.
>
> **Business Info** — major offerings, recent developments, expansion plans.
>
> **Challenges** — *specific* business challenges with reasoning. Look — this isn't generic, it's tied to Adani Realty's specific industry context.
>
> **AI Opportunities** — the most important tab. Each opportunity names the problem solved, the solution, expected impact, and a concrete tech stack. These aren't *'use a chatbot'* — they're things like *'AI-powered floor-plan vectorization for the brochure pipeline'*.
>
> **CEO Pitch** — a one-page personalized pitch addressed to the CEO by name, anchored to the top 3 opportunities. Under 350 words, no fluff.
>
> And there's a **Chat tab** — I can ask follow-up questions, grounded in the report."

**[Type a question: "Which AI opportunity has the highest ROI?"]**

> "The chat agent uses the smaller, faster Llama 3.1 8B model for sub-second answers."

**[Click PDF download]**

> "Finally — I can export the full report as PDF, Markdown, or JSON."

---

### [04:00] Architecture

**[Screen: open `docs/ARCHITECTURE.md` or draw on whiteboard]**

> "Architecturally, this is a **multi-agent pipeline** orchestrated by Python:
>
> 1. **ResearcherAgent** uses Tavily for live web search.
> 2. **AnalystAgent** structures raw evidence into JSON — overview, leadership, key info.
> 3. **StrategistAgent** maps observed challenges to specific AI opportunities.
> 4. **PitchAgent** writes the CEO pitch.
> 5. **ChatAgent** powers the follow-up Q&A.
>
> Each agent has its own narrow system prompt and JSON schema. That separation is critical — it's why each section feels purpose-built rather than generic."

---

### [05:30] AI Tools Used

> "**Tools I deliberately chose:**
>
> - **Groq** for inference because it's the fastest free LLM hosting on the planet — full report in 30–50 seconds.
> - **Llama 3.3 70B** for reasoning because it's open-weight, free, and beats GPT-3.5 on most reasoning benchmarks.
> - **Tavily** over SerpAPI because Tavily is built for AI agents — it returns clean snippets with URLs, not raw HTML.
> - **Streamlit** because it lets me ship a beautiful UI in one file.
> - **Cursor + Claude** as my coding co-pilots throughout development."

---

### [07:00] Challenges & Solutions

> "**Three real problems I ran into:**
>
> 1. **JSON parsing failures.** LLMs sometimes wrap JSON in markdown fences or add preambles. I wrote a `_safe_json` utility that strips fences and falls back to regex-extracting the first `{...}` block.
>
> 2. **Generic AI recommendations.** First versions returned things like *'use a chatbot'*. I fixed this by adding a few-shot specificity example directly in the Strategist's system prompt, with an explicit *good vs bad* contrast.
>
> 3. **Hallucinated leadership names.** The biggest risk. I solved this with three layers: a dedicated leadership Tavily query, an explicit *'use real names ONLY from evidence'* instruction, and a graceful empty-state in the UI when no names are found."

---

### [08:30] Future Work & Wrap-up

> "If I had another week, I'd add:
> - SQLite caching of reports per company
> - LinkedIn profile enrichment via Proxycurl
> - A LangGraph-based retry loop — if leadership is empty, automatically deepen the search
>
> But the current build hits every requirement in the brief — overview, key info, challenges, AI opportunities, personalized pitch — plus chat, PDF export, and a polished dark UI.
>
> Thanks for watching!"

---

## 🎥 Recording Tips

- **Resolution:** 1080p, 30fps minimum
- **Audio:** use a headset mic; record in a quiet room
- **Browser zoom:** 110% — text reads better on video
- **Cursor highlights:** turn on cursor zoom or click-highlight in your screen recorder
- **Edit out** any API key entry in the sidebar before publishing
- **Upload to:** YouTube (unlisted) or Loom; include the link in your submission
