"""
Multi-Agent AI Research & Recommendation System
================================================
Pipeline:
  1. ResearcherAgent  -> Gathers live web data via Tavily
  2. AnalystAgent     -> Extracts company overview, key info, leadership (with sources)
  3. StrategistAgent  -> Identifies challenges (with impact) & AI opportunities (with priority)
  4. SummaryAgent     -> Writes an executive summary grounding all sections
  5. PitchAgent       -> Crafts personalized one-page CEO pitch
"""

import os
import json
import re
from typing import Dict, List, Optional
from groq import Groq
from tavily import TavilyClient


PRIMARY_MODEL = "llama-3.3-70b-versatile"
FAST_MODEL    = "llama-3.1-8b-instant"


class ResearcherAgent:
    def __init__(self, tavily_api_key: str):
        self.client = TavilyClient(api_key=tavily_api_key)

    def _search(self, query: str, max_results: int = 6, depth: str = "advanced") -> Dict:
        try:
            return self.client.search(
                query=query,
                search_depth=depth,
                max_results=max_results,
                include_answer=True,
            )
        except Exception as e:
            return {"error": str(e), "results": [], "answer": ""}

    @staticmethod
    def _merge_searches(searches: List[Dict]) -> Dict:
        """Combine multiple Tavily responses into one section, deduplicating by URL."""
        merged = {"results": [], "answer": ""}
        seen_urls = set()
        answers = []
        for sec in searches:
            if sec.get("answer"):
                answers.append(sec["answer"])
            for r in sec.get("results", []):
                url = r.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    merged["results"].append(r)
        if answers:
            merged["answer"] = "\n".join(answers)
        return merged

    def _leadership_queries(self, company: str) -> List[str]:
        """Tier 1 + Tier 2: targeted exact-match and context queries."""
        return [
            # Tier 1 — exact role queries
            f'"{company}" CEO',
            f'"{company}" founder',
            f'"{company}" chairman',
            f'"{company}" managing director',
            # Tier 2 — context queries
            f'"{company}" leadership team',
            f'"{company}" board of directors',
            f'"{company}" executive team',
            f'{company} about us team leadership',
        ]

    def _supplemental_leadership_queries(self, company: str) -> List[str]:
        """Tier 3: last-resort queries — LinkedIn, MCA filings, databases."""
        return [
            f'"{company}" "CEO" OR "CTO" OR "co-founded by" OR "founded by"',
            f"{company} site:linkedin.com CEO OR CTO OR founder OR co-founder",
            f"{company} private limited directors MCA India CEO managing director",
            f"{company} founder CEO chairman crunchbase tracxn zaubacorp thecompanycheck",
            f"{company} key people management team annual report",
        ]

    def search_leadership(self, company: str, supplemental: bool = False,
                          progress_cb=None) -> Dict:
        queries = (
            self._supplemental_leadership_queries(company)
            if supplemental else self._leadership_queries(company)
        )
        searches = []
        for i, q in enumerate(queries, 1):
            if progress_cb:
                label = "extra leadership" if supplemental else "leadership"
                progress_cb(i / len(queries), f"🔎 Researching: {label} ({i}/{len(queries)})…")
            searches.append(self._search(q, max_results=10))
        return self._merge_searches(searches)

    def gather(self, company: str, progress_cb=None) -> Dict:
        queries = {
            "overview":    f"{company} company overview business model what they do",
            "news":        f"{company} latest news recent developments 2024 2025 expansion announcements",
            "products":    f"{company} products services offerings portfolio",
            "challenges":  f"{company} challenges problems issues complaints customer reviews criticism",
            "financials":  f"{company} revenue financials scale employees market share valuation",
            "competitors": f"{company} competitors industry landscape market position",
            "website":     f"{company} official website linkedin about team",
        }
        total_steps = len(queries) + 1  # +1 for multi-query leadership block
        bundle = {}
        step = 0

        step += 1
        if progress_cb:
            progress_cb(step / total_steps, "🔎 Researching: Leadership…")
        bundle["leadership"] = self.search_leadership(company)

        for label, q in queries.items():
            step += 1
            if progress_cb:
                progress_cb(step / total_steps, f"🔎 Researching: {label.title()}…")
            bundle[label] = self._search(q)
        return bundle


class LLM:
    def __init__(self, api_key: str, model: str = PRIMARY_MODEL):
        self.client = Groq(api_key=api_key)
        self.model = model

    def complete(self, system: str, user: str, json_mode: bool = False,
                 temperature: float = 0.4, max_tokens: int = 2400) -> str:
        kwargs = dict(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        resp = self.client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content


def _format_evidence(bundle: Dict, keys: List[str], char_budget: int = 12000) -> str:
    chunks = []
    for k in keys:
        sec = bundle.get(k, {})
        max_results = 15 if k == "leadership" else 5
        text_limit = 1200 if k == "leadership" else 700
        if sec.get("answer"):
            chunks.append(f"[{k.upper()} — TAVILY ANSWER]\n{sec['answer']}\n")
        for r in sec.get("results", [])[:max_results]:
            title = r.get("title", "")
            url   = r.get("url", "")
            text  = (r.get("content") or "")[:text_limit]
            chunks.append(f"[{k.upper()}] {title}\nURL: {url}\n{text}\n")
    return "\n".join(chunks)[:char_budget]


def _classify_source(url: str) -> str:
    u = url.lower()
    if "linkedin.com" in u:
        return "LinkedIn"
    if any(x in u for x in ["news","times","hindu","economic","mint","reuters","bloomberg","cnbc","forbes","businessline","moneycontrol","livemint"]):
        return "News Article"
    if any(x in u for x in ["gov","sebi","roc","mca","annual","investor","report"]):
        return "Public Report"
    if any(x in u for x in ["crunchbase","tracxn","zaubacorp","tofler","zauba","wikipedia"]):
        return "Business Database"
    return "Company Website"


def _extract_sources(bundle: Dict, keys: List[str], max_per_key: int = 3) -> List[Dict]:
    seen = set()
    sources = []
    for k in keys:
        sec = bundle.get(k, {})
        for r in sec.get("results", [])[:max_per_key]:
            url = r.get("url", "")
            if url and url not in seen:
                seen.add(url)
                sources.append({
                    "url": url,
                    "title": r.get("title", url),
                    "type": _classify_source(url),
                })
    return sources


class AnalystAgent:
    SYSTEM = (
        "You are a senior business analyst writing for a B2B AI consulting firm. "
        "Write crisp, professional, fact-based prose. Never invent facts — "
        "if evidence is missing say 'Not publicly disclosed'. Always return STRICT JSON. "
        "When noting sources for leadership, use the exact URL from the evidence."
    )

    def __init__(self, llm: LLM, researcher: Optional["ResearcherAgent"] = None):
        self.llm = llm
        self.researcher = researcher

    def _extract_leadership(self, company: str, bundle: Dict, char_budget: int = 8000) -> List[Dict]:
        evidence = _format_evidence(bundle, ["leadership"], char_budget=char_budget)
        prompt = f"""You are extracting leadership information for **{company}**.

Your task: find EVERY person mentioned with a leadership role in the evidence below.

Return STRICT JSON:
{{
  "leadership": [
    {{
      "name": "Full Name",
      "role": "Founder | Co-Founder | CEO | CTO | CFO | COO | Chairman | Managing Director | Director | President | VP",
      "bio": "brief background from evidence",
      "source_url": "URL where this person was mentioned"
    }}
  ]
}}

EXTRACTION RULES — FOLLOW EXACTLY:
1. Scan EVERY line of evidence for person names near ANY of these keywords:
   CEO, CTO, CFO, COO, founder, co-founder, chairman, chairperson,
   managing director, MD, director, president, VP, vice president,
   chief executive, chief technology, chief financial, chief operating.
2. Look for these patterns:
   - "Name, Title" or "Name — Title" or "Name (Title)"
   - "Title: Name" or "Title - Name"
   - "founded by Name" or "co-founded by Name"
   - "Name is the CEO" or "Name serves as"
   - "Name, who leads" or "Name heads"
   - LinkedIn snippets: "Name · Title at {company}"
   - MCA/ROC: "Director: Name"
3. Include PARTIAL names if that is all the evidence has (e.g., "Mr. Sharma" is valid).
4. If a person has multiple roles, list the most senior one.
5. NEVER return an empty leadership array if there is ANY name near ANY title keyword.
6. For source_url, use the URL line closest to where the name appeared.

EVIDENCE:
{evidence}
"""
        raw = self.llm.complete(self.SYSTEM, prompt, json_mode=True, temperature=0.1, max_tokens=1800)
        return _sanitize_leadership(_safe_json(raw).get("leadership", []))

    def analyze(self, company: str, bundle: Dict) -> Dict:
        evidence = _format_evidence(
            bundle, ["overview","products","news","financials","leadership","website"],
            char_budget=14000,
        )
        prompt = f"""Analyze **{company}** using ONLY the evidence below.

Return STRICT JSON with this exact schema:
{{
  "overview": {{
     "what_they_do": "2-3 sentence summary of the business model",
     "industry": "primary industry / sector",
     "scale": "size indicators: employees, revenue, locations if known",
     "geographic_presence": "regions / countries / cities of operation",
     "founded": "year founded or 'Not publicly disclosed'",
     "headquarters": "city, country or 'Not publicly disclosed'",
     "website": "official website URL or 'Not publicly disclosed'"
  }},
  "key_business_info": {{
     "major_offerings": ["bullet 1", "bullet 2", "bullet 3", "bullet 4"],
     "recent_developments": ["bullet 1", "bullet 2", "bullet 3"],
     "expansion_plans": ["bullet 1", "bullet 2"],
     "notable_public_info": ["bullet 1", "bullet 2"]
  }},
  "leadership": [
     {{
        "name": "Full Name — MUST be a real person name found in the evidence",
        "role": "Founder | Co-Founder | CEO | CTO | CFO | COO | Chairman | Managing Director | Director | President | VP",
        "bio": "1-2 sentences: their background, years in role, or prior company if found in evidence",
        "source_url": "The exact URL from the evidence where this person's name was mentioned."
     }}
  ],
  "sources": [
     {{"url": "url_string", "title": "page title", "type": "Company Website | LinkedIn | News Article | Public Report | Business Database"}}
  ]
}}

LEADERSHIP EXTRACTION RULES (CRITICAL — follow exactly):
1. Scan EVERY section of the evidence (overview, products, news, financials, leadership, website) for person names near leadership titles.
2. Leadership titles to look for: CEO, CTO, CFO, COO, Founder, Co-Founder, Chairman, Chairperson, Managing Director, MD, Director, President, VP, Vice President, Chief Executive, Chief Technology Officer, Chief Financial Officer.
3. Name patterns to match:
   - "Name, Title" or "Name — Title" or "Name (Title)"
   - "Title: Name" or "Title - Name"
   - "founded by Name" or "co-founded by Name"
   - "Name is the CEO" or "Name serves as"
   - "Name heads" or "Name leads" or "under Name's leadership"
   - LinkedIn: "Name · Title at {company}"
   - MCA/ROC: "Director: Name"
4. Prioritize: Founder/Co-Founder first, then CEO, CTO/CFO/COO, Chairman/MD, Directors.
5. Include partial names (e.g., "Mr. Sharma") if that's all available.
6. NEVER return an empty leadership array if ANY person name appears near any title in the evidence.
7. For source_url, use the URL from the evidence chunk where the name appeared.
8. Real names ONLY — never invent names. But search ALL evidence chunks thoroughly.

SOURCES RULES:
- Include 5-10 diverse URLs. Classify each type accurately.

EVIDENCE:
{evidence}
"""
        raw = self.llm.complete(self.SYSTEM, prompt, json_mode=True, temperature=0.2, max_tokens=3500)
        result = _safe_json(raw)

        # ── Multi-pass leadership extraction ──────────────────────────────────
        leaders_found = _sanitize_leadership(result.get("leadership", []))

        # Pass 2: Dedicated leadership extraction if < 3 leaders found
        if len(leaders_found) < 3:
            extra_leaders = self._extract_leadership(company, bundle, char_budget=8000)
            leaders_found = _merge_leaders(leaders_found, extra_leaders)

        # Pass 3: Supplemental web search if < 2 leaders found
        if len(leaders_found) < 2 and self.researcher:
            extra = self.researcher.search_leadership(company, supplemental=True)
            existing = bundle.get("leadership", {})
            bundle["leadership"] = ResearcherAgent._merge_searches([existing, extra])
            extra_leaders = self._extract_leadership(company, bundle, char_budget=12000)
            leaders_found = _merge_leaders(leaders_found, extra_leaders)

        # Graceful degradation: never leave leadership completely empty
        if not leaders_found:
            leaders_found = [{
                "name": "Leadership information not verified",
                "role": "See sources for further research",
                "bio": (
                    f"Multiple search strategies were attempted for {company}. "
                    "Check the official company website, LinkedIn page, "
                    "or MCA/ROC filings for the latest leadership information."
                ),
                "source_url": "",
            }]

        result["leadership"] = leaders_found

        # Supplement sources with raw Tavily URLs
        if not result.get("sources"):
            result["sources"] = []
        existing_urls = {s.get("url") for s in result["sources"]}
        for ts in _extract_sources(bundle, ["overview","leadership","news","financials","website","products"]):
            if ts["url"] not in existing_urls:
                result["sources"].append(ts)
                existing_urls.add(ts["url"])

        return result


class StrategistAgent:
    SYSTEM = (
        "You are an AI solutions strategist who reasons like a McKinsey principal. "
        "Connect observed company facts — industry, scale, operations, expansion — "
        "to SPECIFIC business challenges and CONCRETE AI recommendations. "
        "Generic outputs like 'use a chatbot' or 'improve customer service' are forbidden. "
        "Always tie recommendations to this company's exact industry, scale, and pain points. "
        "Always return STRICT JSON."
    )

    def __init__(self, llm: LLM):
        self.llm = llm

    def strategize(self, company: str, analyst_output: Dict, bundle: Dict) -> Dict:
        evidence = _format_evidence(bundle, ["challenges","news","products","competitors","financials"])
        ctx = (json.dumps(analyst_output.get("overview", {}), indent=2) + "\n" +
               json.dumps(analyst_output.get("key_business_info", {}), indent=2))

        prompt = f"""Company: **{company}**

Known facts:
{ctx}

Additional evidence:
{evidence}

Produce STRICT JSON:
{{
  "challenges": [
     {{
        "title": "Short specific challenge name",
        "category": "Operational | Sales | Customer Experience | Technology | Market | Regulatory",
        "description": "2-3 sentences describing the challenge in this company's specific context",
        "reasoning": "Why this challenge exists for THIS company — cite specific facts: their industry, scale, expansion, or observed complaints",
        "impact": "How this challenge concretely affects revenue, operations, sales pipeline, or customer retention — be specific"
     }}
  ],
  "ai_opportunities": [
     {{
        "title": "Specific AI solution name",
        "problem_solved": "Which specific challenge this addresses",
        "implementation_idea": "2-3 sentences on HOW to implement this: name the workflow, data sources, and integration points specific to this company",
        "expected_business_impact": "Specific quantifiable or qualitative impact — e.g., '30% reduction in manual processing time', 'reduce churn by identifying at-risk accounts early'",
        "tech_stack": "Specific tech: e.g., 'RAG pipeline + LlamaIndex + GPT-4 + Pinecone', 'YOLOv8 for quality inspection', 'Prophet/LSTM for demand forecasting on SKU-level POS data'",
        "priority": "High | Medium | Low",
        "priority_reasoning": "One sentence on ROI, feasibility, and urgency for this priority level"
     }}
  ]
}}

Rules:
- 4-6 challenges. Every challenge must cite observable company-specific reasoning AND state concrete business impact.
- 4-6 AI opportunities. Every opportunity must name a specific implementation workflow and real tech stack.
- Priority High = addresses revenue/cost directly, technically feasible today.
- Good specificity: "AI floor-plan vectorization for {company}'s brochure pipeline using LayoutLMv3" — not "use AI for documents".
"""
        raw = self.llm.complete(self.SYSTEM, prompt, json_mode=True, temperature=0.5, max_tokens=3500)
        return _safe_json(raw)


class SummaryAgent:
    SYSTEM = (
        "You are a management consultant writing an executive briefing note. "
        "Synthesize research findings into a sharp, authoritative summary "
        "that a CEO or investor could read in 60 seconds. Be specific and data-grounded. "
        "Avoid filler phrases. Never say 'In conclusion' or 'It is worth noting'."
    )

    def __init__(self, llm: LLM):
        self.llm = llm

    def summarize(self, company: str, analyst: Dict, strategy: Dict) -> str:
        ov = analyst.get("overview", {})
        top_challenges = strategy.get("challenges", [])[:3]
        top_opps = strategy.get("ai_opportunities", [])[:3]
        high_prio = [o for o in top_opps if o.get("priority") == "High"]

        ch_names = "; ".join(c.get("title", "") for c in top_challenges)
        opp_names = "; ".join(o.get("title", "") for o in top_opps)

        prompt = f"""Write an Executive Summary for **{company}**.

Company context:
- What they do: {ov.get('what_they_do','N/A')}
- Industry: {ov.get('industry','N/A')}
- Scale: {ov.get('scale','N/A')}
- HQ: {ov.get('headquarters','N/A')}
- Geographic presence: {ov.get('geographic_presence','N/A')}

Top challenges: {ch_names}
Top AI opportunities: {opp_names}
High-priority opportunities: {", ".join(o.get("title","") for o in high_prio) or "None"}

Write exactly 3 paragraphs:
1. **Who they are** — company identity, business model, market position, and scale.
2. **Where the pressure is** — the 2-3 most significant business challenges and why they matter NOW.
3. **Where AI can win** — the 2-3 highest-impact AI opportunities, framed as business outcomes not tech. End with one sentence on the strategic window.

Tone: authoritative, specific, zero filler. Under 220 words total.
"""
        return self.llm.complete(self.SYSTEM, prompt, temperature=0.4, max_tokens=700)


class PitchAgent:
    SYSTEM = (
        "You are an elite enterprise-sales copywriter writing one-page CEO pitches. "
        "Sound human, confident, and specific — never templated. "
        "Never use: 'I hope this email finds you well', 'As per my research', 'I wanted to reach out', "
        "'touch base', 'synergies', or any other corporate cliché."
    )

    def __init__(self, llm: LLM):
        self.llm = llm

    def write(self, company: str, analyst: Dict, strategy: Dict) -> str:
        ceo_name = "the CEO"
        leaders = analyst.get("leadership", [])
        for p in leaders:
            if "ceo" in (p.get("role", "").lower()):
                ceo_name = p.get("name", "the CEO")
                break
        if ceo_name == "the CEO":
            for p in leaders:
                role = (p.get("role") or "").lower()
                if "founder" in role or "managing director" in role or role == "md":
                    ceo_name = p.get("name", "the CEO")
                    break

        top_opps = strategy.get("ai_opportunities", [])[:3]
        opps_str = "\n".join(
            f"- {o.get('title')}: {o.get('problem_solved')} → {o.get('expected_business_impact','')}"
            for o in top_opps
        )
        recent = analyst.get("key_business_info", {}).get("recent_developments", [])
        recent_hook = recent[0] if recent else f"{company}'s current growth phase"

        prompt = f"""Write a one-page personalized outreach pitch addressed to **{ceo_name}** at **{company}**.

Use this structure with these exact markdown headings:

### Subject Line
(Specific and intriguing — reference something real about the company)

### Opening
(2-3 sentences. Hook with something specific and recent: "{recent_hook}". Show you understand their world. No generic openers.)

### What I See
(2-3 sentences naming the top 2 business challenges — use industry language, sound like you did real homework)

### How AI Can Change the Equation
(Reference these specific opportunities as executive-level business outcomes for {company}:
{opps_str}
Write 3-4 sentences. Be specific about business impact.)

### Why Now
(1-2 sentences on the competitive window — why acting on AI now matters specifically for {company})

### Suggested Next Step
(One clear, low-friction ask — a 20-min discovery call or no-commitment pilot scoping)

### Sign-off
Warm regards,
[Your Name]
AI Solutions Consultant

Under 380 words total. Sound like you actually know the company.
"""
        return self.llm.complete(self.SYSTEM, prompt, temperature=0.7, max_tokens=1400)


class ChatAgent:
    SYSTEM = (
        "You are a helpful research assistant and business analyst. "
        "Answer questions using the intelligence report as primary context. "
        "Be specific, cite sections when relevant. If the answer isn't in the report, "
        "say so honestly and suggest what additional research would help. "
        "You may provide informed analysis when clearly labeled as such."
    )

    def __init__(self, api_key: str):
        self.llm = LLM(api_key, model=FAST_MODEL)

    def reply(self, report_context: str, history: List[Dict], user_msg: str) -> str:
        convo = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in history[-6:])
        user_block = f"""INTELLIGENCE REPORT CONTEXT:
\"\"\"{report_context[:8000]}\"\"\"

CONVERSATION SO FAR:
{convo}

NEW USER QUESTION: {user_msg}
"""
        return self.llm.complete(self.SYSTEM, user_block, temperature=0.4, max_tokens=900)


class ResearchOrchestrator:
    def __init__(self, groq_key: str, tavily_key: str):
        self.researcher = ResearcherAgent(tavily_key)
        self.llm = LLM(groq_key, model=PRIMARY_MODEL)
        self.analyst = AnalystAgent(self.llm, researcher=self.researcher)
        self.strategist = StrategistAgent(self.llm)
        self.summarizer = SummaryAgent(self.llm)
        self.pitch = PitchAgent(self.llm)

    def run(self, company: str, progress_cb=None) -> Dict:
        if progress_cb: progress_cb(0.05, "🌐 Connecting to research sources…")
        bundle = self.researcher.gather(
            company,
            progress_cb=lambda p, m: progress_cb(0.05 + p * 0.40, m) if progress_cb else None,
        )

        if progress_cb: progress_cb(0.50, "🧠 Analyzing company fundamentals…")
        analyst_out = self.analyst.analyze(company, bundle)

        if progress_cb: progress_cb(0.68, "♟️ Strategizing AI opportunities…")
        strategy_out = self.strategist.strategize(company, analyst_out, bundle)

        if progress_cb: progress_cb(0.84, "📝 Writing executive summary…")
        summary_out = self.summarizer.summarize(company, analyst_out, strategy_out)

        if progress_cb: progress_cb(0.93, "✍️ Drafting personalized CEO pitch…")
        pitch_out = self.pitch.write(company, analyst_out, strategy_out)

        if progress_cb: progress_cb(1.0, "✅ Report ready.")
        return {
            "company": company,
            "executive_summary": summary_out,
            "analyst": analyst_out,
            "strategy": strategy_out,
            "pitch": pitch_out,
            "raw_bundle": bundle,
        }


def _strip_html(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", str(text))
    return re.sub(r"\s+", " ", text).strip()


def _sanitize_leadership(leaders: List[Dict]) -> List[Dict]:
    cleaned = []
    seen = set()
    skip_names = {
        "unknown", "n/a", "not publicly disclosed", "not available",
        "not found", "none", "no information", "undisclosed",
    }
    for p in leaders or []:
        name = _strip_html(p.get("name", ""))
        role = _strip_html(p.get("role", ""))
        bio = _strip_html(p.get("bio", ""))
        if not name or name.lower().strip() in skip_names:
            continue
        if any(x in f"{name} {role} {bio}".lower() for x in ("<div", "class=", "leader-card", "leader-name")):
            continue
        # Skip entries that are clearly not person names
        if len(name) < 2 or name.startswith("http"):
            continue
        key = name.lower().strip()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append({
            "name": name,
            "role": role,
            "bio": bio,
            "source_url": (p.get("source_url") or "").strip(),
        })
    return cleaned


def _merge_leaders(existing: List[Dict], new: List[Dict]) -> List[Dict]:
    """Merge two leadership lists, deduplicating by name."""
    seen = {p["name"].lower().strip() for p in existing}
    merged = list(existing)
    for p in new:
        key = p["name"].lower().strip()
        if key not in seen:
            seen.add(key)
            merged.append(p)
    return merged


def _safe_json(raw: str) -> Dict:
    if not raw:
        return {}
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?", "", raw).strip()
    raw = re.sub(r"```$", "", raw).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", raw)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    return {"_parse_error": True, "_raw": raw[:500]}
