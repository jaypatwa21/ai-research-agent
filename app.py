"""
AI-Powered Research & Recommendation Agent
==========================================
Streamlit application — dark themed, gradient UI, multi-agent backend.
"""

import os
import time
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from agents import ResearchOrchestrator, ChatAgent
from exporter import to_markdown, to_pdf

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Research Agent · Intelligence Reports",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS — keep the existing premium dark UI, add source badges + priority badges
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}

.stApp {
    background:
        radial-gradient(1200px 600px at 10% -10%, rgba(139,92,246,0.18), transparent 60%),
        radial-gradient(900px 500px at 110% 10%, rgba(59,130,246,0.14), transparent 60%),
        radial-gradient(800px 400px at 50% 120%, rgba(236,72,153,0.10), transparent 60%),
        #0a0a0f;
    color: #e5e7eb;
}

.hero {
    background: linear-gradient(135deg, rgba(139,92,246,0.12), rgba(59,130,246,0.10));
    border: 1px solid rgba(139,92,246,0.25);
    border-radius: 20px; padding: 32px 36px; margin-bottom: 24px;
    backdrop-filter: blur(10px);
}
.hero h1 {
    font-size: 2.4rem;
    background: linear-gradient(90deg, #a78bfa, #60a5fa, #f472b6);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0; font-weight: 800; letter-spacing: -0.5px;
}
.hero p { color: #9ca3af; margin-top: 8px; font-size: 1.05rem; }
.hero .badge {
    display: inline-block; padding: 4px 10px; border-radius: 999px;
    background: rgba(139,92,246,0.2); color: #c4b5fd; font-size: 0.75rem;
    font-weight: 600; margin-right: 6px; margin-top: 10px;
}

.card {
    background: rgba(19,19,26,0.7);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px; padding: 22px 26px; margin-bottom: 18px;
    backdrop-filter: blur(8px);
}
.card h2 { color: #e5e7eb; font-size: 1.4rem; margin-top: 0; border-left: 4px solid #8b5cf6; padding-left: 12px; }

/* Executive Summary */
.exec-summary {
    background: linear-gradient(135deg, rgba(59,130,246,0.10), rgba(139,92,246,0.08));
    border: 1px solid rgba(59,130,246,0.3);
    border-radius: 16px; padding: 26px 30px; margin-bottom: 20px;
}
.exec-summary h2 { color: #93c5fd; font-size: 1.3rem; margin-top: 0; }
.exec-summary p { color: #e5e7eb; line-height: 1.7; margin: 0; }

/* Leader cards */
.leader-grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 14px; margin: 12px 0;
}
.leader-card {
    background: linear-gradient(135deg, rgba(139,92,246,0.10), rgba(59,130,246,0.06));
    border: 1px solid rgba(139,92,246,0.25); border-radius: 14px; padding: 18px;
}
.leader-avatar {
    width: 54px; height: 54px; border-radius: 50%;
    background: linear-gradient(135deg, #8b5cf6, #3b82f6);
    color: white; display: flex; align-items: center; justify-content: center;
    font-size: 1.4rem; font-weight: 700; margin-bottom: 10px;
}
.leader-name { font-weight: 700; color: #f3f4f6; font-size: 1.05rem; }
.leader-role { color: #a78bfa; font-size: 0.85rem; font-weight: 600; margin-bottom: 8px; }
.leader-bio { color: #9ca3af; font-size: 0.85rem; line-height: 1.45; }
.leader-source { font-size: 0.75rem; margin-top: 8px; }
.leader-source a { color: #60a5fa; text-decoration: none; }

/* Challenge cards */
.challenge-card {
    background: rgba(239,68,68,0.05); border-left: 3px solid #ef4444;
    padding: 14px 18px; border-radius: 8px; margin-bottom: 10px;
}
.challenge-card .cat {
    display: inline-block; font-size: 0.7rem; padding: 2px 8px;
    background: rgba(239,68,68,0.18); color: #fca5a5;
    border-radius: 999px; font-weight: 600; margin-bottom: 6px;
}
.challenge-impact {
    background: rgba(251,191,36,0.08); border-left: 2px solid #fbbf24;
    padding: 6px 10px; border-radius: 4px; margin-top: 8px;
    color: #fde68a; font-size: 0.88rem;
}

/* Opportunity cards */
.opp-card {
    background: rgba(16,185,129,0.05); border-left: 3px solid #10b981;
    padding: 14px 18px; border-radius: 8px; margin-bottom: 12px;
}
.opp-card .stack {
    background: rgba(16,185,129,0.12); color: #6ee7b7;
    padding: 3px 8px; border-radius: 6px; font-family: monospace; font-size: 0.78rem;
}
.priority-high   { display:inline-block; padding:2px 10px; border-radius:999px; font-size:0.72rem; font-weight:700; background:rgba(239,68,68,0.2); color:#fca5a5; margin-left:8px; }
.priority-medium { display:inline-block; padding:2px 10px; border-radius:999px; font-size:0.72rem; font-weight:700; background:rgba(251,191,36,0.2); color:#fde68a; margin-left:8px; }
.priority-low    { display:inline-block; padding:2px 10px; border-radius:999px; font-size:0.72rem; font-weight:700; background:rgba(107,114,128,0.3); color:#d1d5db; margin-left:8px; }

/* Source badges */
.source-row { display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }
.source-badge {
    display:inline-flex; align-items:center; gap:5px;
    background: rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1);
    border-radius:8px; padding:5px 10px; font-size:0.78rem;
    color:#d1d5db; text-decoration:none; max-width:320px; overflow:hidden;
    white-space:nowrap; text-overflow:ellipsis;
}
.source-badge:hover { background:rgba(139,92,246,0.15); border-color:rgba(139,92,246,0.4); }
.src-type { font-size:0.68rem; color:#a78bfa; font-weight:700; }

/* Pitch */
.pitch-card {
    background: linear-gradient(135deg, rgba(139,92,246,0.12), rgba(236,72,153,0.08));
    border: 1px solid rgba(236,72,153,0.25); border-radius: 16px; padding: 26px 30px; color: #e5e7eb;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #8b5cf6, #6366f1) !important;
    color: white !important; border: none !important; border-radius: 10px !important;
    padding: 10px 22px !important; font-weight: 600 !important; transition: all 0.2s !important;
}
.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(139,92,246,0.4) !important; }

.stTextInput > div > div > input {
    background: rgba(255,255,255,0.04) !important; border: 1px solid rgba(139,92,246,0.3) !important;
    color: #f3f4f6 !important; border-radius: 10px !important;
}

.stTabs [data-baseweb="tab-list"] { gap: 4px; background: rgba(19,19,26,0.5); padding: 6px; border-radius: 12px; }
.stTabs [data-baseweb="tab"] { background: transparent; color: #9ca3af; border-radius: 8px; padding: 8px 16px; font-weight: 600; }
.stTabs [aria-selected="true"] { background: linear-gradient(135deg, #8b5cf6, #6366f1) !important; color: white !important; }

[data-testid="stSidebar"] { background: rgba(10,10,15,0.92) !important; border-right: 1px solid rgba(139,92,246,0.15); }

.stChatMessage { background: rgba(19,19,26,0.6) !important; border-radius: 12px; }
.footer { text-align:center; color:#6b7280; padding:24px 0 10px; font-size:0.85rem; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────────────────────────────────────
if "report" not in st.session_state:
    st.session_state.report = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
# ─────────────────────────────────────────────────────────────────────────────
# Sidebar — API keys & settings
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔑 API Configuration")
    st.caption("Keys are kept in session memory — never persisted server-side.")

    use_demo = st.checkbox(
        "Use Demo Keys (from environment)",
        value=bool(os.getenv("GROQ_API_KEY") and os.getenv("TAVILY_API_KEY")),
        help="If checked, the app uses GROQ_API_KEY and TAVILY_API_KEY from the .env file / environment.",
    )

    if use_demo:
        groq_key   = os.getenv("GROQ_API_KEY", "")
        tavily_key = os.getenv("TAVILY_API_KEY", "")
        if groq_key and tavily_key:
            st.success("✅ Demo keys loaded from environment")
        else:
            st.warning("⚠️ Demo keys not found in environment — please enter them below.")
            use_demo = False

    if not use_demo:
        groq_key = st.text_input(
            "Groq API Key", value=os.getenv("GROQ_API_KEY", ""),
            type="password", help="Free at https://console.groq.com/keys",
        )
        tavily_key = st.text_input(
            "Tavily API Key", value=os.getenv("TAVILY_API_KEY", ""),
            type="password", help="Free at https://app.tavily.com/",
        )

    st.markdown("---")
    st.markdown("### 🧠 Tech Stack")
    st.markdown(
        "- **LLM:** Groq · Llama 3.3 70B\n"
        "- **Fast LLM:** Llama 3.1 8B Instant\n"
        "- **Search:** Tavily AI (10+ queries)\n"
        "- **UI:** Streamlit\n"
        "- **PDF:** ReportLab"
    )

    if st.session_state.report:
        st.markdown("---")
        if st.button("🗑️ Clear Report", use_container_width=True):
            st.session_state.report = None
            st.session_state.chat_history = []
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Hero
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>🧠 AI Research & Recommendation Agent</h1>
  <p>Generate institutional-grade company intelligence reports in under a minute.
  Live web research · AI-driven analysis · Personalized CEO pitches.</p>
  <span class="badge">⚡ Multi-Agent Pipeline</span>
  <span class="badge">🌐 Live Web Data</span>
  <span class="badge">💡 AI Opportunity Mapping</span>
  <span class="badge">📄 PDF + MD Export</span>
  <span class="badge">💬 Chat with Report</span>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Input section
# ─────────────────────────────────────────────────────────────────────────────
col_input, col_btn = st.columns([4, 1])
with col_input:
    company = st.text_input(
        "Company name",
        placeholder="e.g., Adani Realty, Sobha, Tata Steel, Zomato…",
        label_visibility="collapsed",
    )
with col_btn:
    run_btn = st.button("🚀 Generate Report", use_container_width=True, type="primary")

st.markdown("**Quick examples:**")
preset_cols = st.columns(6)
PRESETS = ["Adani Realty", "Sobha Limited", "Tata Steel", "Zomato", "Paytm", "Reliance Jio"]
for i, name in enumerate(PRESETS):
    with preset_cols[i]:
        if st.button(name, key=f"preset_{i}", use_container_width=True):
            st.session_state["_preset_choice"] = name
            st.rerun()
if "_preset_choice" in st.session_state and not company:
    company = st.session_state.pop("_preset_choice")
    run_btn = True


# ─────────────────────────────────────────────────────────────────────────────
# Run pipeline
# ─────────────────────────────────────────────────────────────────────────────
def _validate_keys() -> bool:
    if not groq_key:
        st.error("🔑 Please add your **Groq API key** in the sidebar. Get one free at https://console.groq.com/keys")
        return False
    if not tavily_key:
        st.error("🔑 Please add your **Tavily API key** in the sidebar. Get one free at https://app.tavily.com/")
        return False
    return True


if run_btn and company.strip():
    if not _validate_keys():
        st.stop()

    progress = st.progress(0, text="Starting…")
    status = st.empty()

    def cb(p, msg):
        progress.progress(min(p, 1.0), text=msg)
        status.markdown(f"<div style='color:#a78bfa;font-weight:600;'>{msg}</div>", unsafe_allow_html=True)

    try:
        orchestrator = ResearchOrchestrator(groq_key, tavily_key)
        t0 = time.time()
        report = orchestrator.run(company.strip(), progress_cb=cb)
        report["_elapsed"] = round(time.time() - t0, 1)
        st.session_state.report = report
        st.session_state.chat_history = []
        progress.empty()
        status.empty()
        st.success(f"✅ Report generated in {report['_elapsed']}s")
        time.sleep(0.4)
        st.rerun()
    except Exception as e:
        progress.empty()
        status.empty()
        st.error(f"❌ Something went wrong: {e}")
        st.exception(e)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _esc_html(text: str) -> str:
    if not text:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _clean_leaders(leaders: list) -> list:
    """Keep only real person entries — drop HTML fragments or empty placeholders."""
    cleaned = []
    seen = set()
    for p in leaders:
        name = (p.get("name") or "").strip()
        role = (p.get("role") or "").strip()
        bio = (p.get("bio") or "").strip()
        if not name or name.lower() in ("unknown", "n/a", "not publicly disclosed"):
            continue
        blob = f"{name} {role} {bio}".lower()
        if any(x in blob for x in ("<div", "class=", "leader-card", "leader-name", "{", "}")):
            continue
        key = name.lower()
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


def _priority_badge(p: str) -> str:
    cls = {"high": "priority-high", "medium": "priority-medium", "low": "priority-low"}.get(p.lower(), "priority-low")
    return f'<span class="{cls}">{"🔴" if p=="High" else "🟡" if p=="Medium" else "🔵"} {p}</span>'


SOURCE_ICONS = {
    "LinkedIn": "🔗",
    "News Article": "📰",
    "Public Report": "📑",
    "Business Database": "🗂️",
    "Company Website": "🌐",
}


def _render_sources(sources: list):
    if not sources:
        st.caption("_No sources captured._")
        return
    html = '<div class="source-row">'
    for s in sources[:16]:
        icon = SOURCE_ICONS.get(s.get("type", ""), "🌐")
        title = (s.get("title") or s.get("url", ""))[:55]
        url = s.get("url", "#")
        stype = s.get("type", "")
        html += f'<a href="{url}" target="_blank" class="source-badge">{icon} <span><span class="src-type">{stype}</span><br>{title}</span></a>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Render report
# ─────────────────────────────────────────────────────────────────────────────
def render_report(report: dict):
    a = report.get("analyst", {})
    s = report.get("strategy", {})
    company = report["company"]
    ov = a.get("overview", {})
    kb = a.get("key_business_info", {})
    leaders = a.get("leadership", [])
    sources = a.get("sources", [])
    exec_summary = report.get("executive_summary", "")

    # Header
    st.markdown(f"""
    <div class="card">
      <h2>📊 {company} — Intelligence Report</h2>
      <p style='color:#9ca3af; margin:6px 0 0;'>Generated {datetime.now().strftime("%B %d, %Y at %H:%M")} ·
      Completed in {report.get('_elapsed', '?')}s</p>
    </div>
    """, unsafe_allow_html=True)

    # Executive Summary (always visible above tabs)
    if exec_summary:
        paras = [p.strip() for p in exec_summary.split("\n\n") if p.strip()]
        paras_html = "".join(f"<p>{p}</p>" for p in paras)
        st.markdown(f"""
        <div class="exec-summary">
          <h2>📋 Executive Summary</h2>
          {paras_html}
        </div>
        """, unsafe_allow_html=True)

    tabs = st.tabs([
        "🏢 Overview", "👥 Leadership", "📦 Business Info",
        "⚠️ Challenges", "💡 AI Opportunities", "🎯 CEO Pitch",
        "🔗 Sources", "💬 Chat",
    ])

    # ── Overview ──────────────────────────────────────────────────────────────
    with tabs[0]:
        st.markdown('<div class="card"><h2>🏢 Company Overview</h2>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**What they do**  \n{ov.get('what_they_do','N/A')}")
            st.markdown(f"**Industry**  \n{ov.get('industry','N/A')}")
            st.markdown(f"**Founded**  \n{ov.get('founded','N/A')}")
            if ov.get("website") and ov["website"] != "Not publicly disclosed":
                st.markdown(f"**Website**  \n[{ov['website']}]({ov['website']})")
        with c2:
            st.markdown(f"**Scale**  \n{ov.get('scale','N/A')}")
            st.markdown(f"**Geographic Presence**  \n{ov.get('geographic_presence','N/A')}")
            st.markdown(f"**Headquarters**  \n{ov.get('headquarters','N/A')}")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Leadership ────────────────────────────────────────────────────────────
    with tabs[1]:
        st.markdown('<div class="card"><h2>👥 Leadership Team</h2>', unsafe_allow_html=True)
        valid_leaders = _clean_leaders(leaders)
        if valid_leaders:
            cols = st.columns(min(len(valid_leaders), 3))
            for i, p in enumerate(valid_leaders):
                name = _esc_html(p["name"])
                role = _esc_html(p["role"])
                bio = _esc_html(p["bio"])
                src = p.get("source_url", "")
                src_html = (
                    f'<div class="leader-source">📎 <a href="{_esc_html(src)}" target="_blank">Source</a></div>'
                    if src else ""
                )
                with cols[i % len(cols)]:
                    st.markdown(
                        f"""<div class="leader-card">
                            <div class="leader-name">{name}</div>
                            <div class="leader-role">{role}</div>
                            <div class="leader-bio">{bio}</div>
                            {src_html}
                        </div>""",
                        unsafe_allow_html=True,
                    )
        else:
            st.info(
                "No CEO/CTO names were found in publicly indexed sources. "
                "Try the exact legal name (e.g. 'Unada Labs Private Limited') or check the company's LinkedIn / website About page."
            )
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Business Info ─────────────────────────────────────────────────────────
    with tabs[2]:
        st.markdown('<div class="card"><h2>📦 Key Business Information</h2>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### 🛍️ Major Offerings")
            for x in kb.get("major_offerings", []) or ["_Not publicly disclosed_"]:
                st.markdown(f"- {x}")
            st.markdown("##### 📈 Expansion Plans")
            for x in kb.get("expansion_plans", []) or ["_Not publicly disclosed_"]:
                st.markdown(f"- {x}")
        with c2:
            st.markdown("##### 📰 Recent Developments")
            for x in kb.get("recent_developments", []) or ["_Not publicly disclosed_"]:
                st.markdown(f"- {x}")
            st.markdown("##### ℹ️ Notable Public Info")
            for x in kb.get("notable_public_info", []) or ["_Not publicly disclosed_"]:
                st.markdown(f"- {x}")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Challenges ────────────────────────────────────────────────────────────
    with tabs[3]:
        st.markdown('<div class="card"><h2>⚠️ Potential Business Challenges</h2>', unsafe_allow_html=True)
        for i, c in enumerate(s.get("challenges", []), 1):
            impact_html = ""
            if c.get("impact"):
                impact_html = f'<div class="challenge-impact">📊 <b>Business Impact:</b> {c["impact"]}</div>'
            st.markdown(f"""
            <div class="challenge-card">
              <span class="cat">{c.get('category','')}</span>
              <h4 style='margin:4px 0; color:#fca5a5;'>{i}. {c.get('title','Untitled')}</h4>
              <div style='color:#e5e7eb; margin:6px 0;'>{c.get('description','')}</div>
              <div style='color:#9ca3af; font-style:italic; font-size:0.9rem; margin-top:6px;'>
                <b style='color:#f87171;'>Reasoning:</b> {c.get('reasoning','')}
              </div>
              {impact_html}
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── AI Opportunities ──────────────────────────────────────────────────────
    with tabs[4]:
        st.markdown('<div class="card"><h2>💡 AI Opportunities</h2>', unsafe_allow_html=True)
        for i, o in enumerate(s.get("ai_opportunities", []), 1):
            prio = o.get("priority", "Medium")
            prio_badge = _priority_badge(prio)
            prio_reason = o.get("priority_reasoning", "")
            impl = o.get("implementation_idea", o.get("solution", ""))
            impact = o.get("expected_business_impact", o.get("expected_impact", ""))
            st.markdown(f"""
            <div class="opp-card">
              <h4 style='margin:0; color:#6ee7b7;'>💡 {i}. {o.get('title','Untitled')} {prio_badge}</h4>
              <div style='color:#e5e7eb; margin-top:10px;'>
                <b>Problem Solved:</b> {o.get('problem_solved','')}<br><br>
                <b>Implementation Idea:</b> {impl}<br><br>
                <b>Expected Business Impact:</b> {impact}<br><br>
                <b>Tech Stack:</b> <span class="stack">{o.get('tech_stack','')}</span><br>
                <span style='color:#9ca3af; font-size:0.83rem; margin-top:6px; display:block;'>
                  <i>Priority Reasoning: {prio_reason}</i>
                </span>
              </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── CEO Pitch ─────────────────────────────────────────────────────────────
    with tabs[5]:
        st.markdown('<div class="pitch-card">', unsafe_allow_html=True)
        st.markdown("### 🎯 Personalized Pitch to the CEO")
        st.markdown(report.get("pitch", ""))
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Sources ───────────────────────────────────────────────────────────────
    with tabs[6]:
        st.markdown('<div class="card"><h2>🔗 Research Sources</h2>', unsafe_allow_html=True)
        st.caption(f"The report was compiled from {len(sources)} indexed sources across web search, LinkedIn, news, and public databases.")

        # Group by type
        from collections import defaultdict
        by_type = defaultdict(list)
        for s_ in sources:
            by_type[s_.get("type", "Other")].append(s_)

        type_order = ["Company Website", "LinkedIn", "News Article", "Public Report", "Business Database", "Other"]
        for t in type_order:
            if by_type[t]:
                icon = SOURCE_ICONS.get(t, "🌐")
                st.markdown(f"**{icon} {t}** ({len(by_type[t])})")
                _render_sources(by_type[t])
                st.markdown("")

        st.markdown('</div>', unsafe_allow_html=True)

    # ── Chat ──────────────────────────────────────────────────────────────────
    with tabs[7]:
        st.markdown("### 💬 Ask follow-up questions about this report")
        st.caption("The assistant is grounded in the report above. It can also offer additional analysis.")

        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

        user_q = st.chat_input("Ask anything about the company or the report…")
        if user_q:
            st.session_state.chat_history.append({"role": "user", "content": user_q})
            with st.chat_message("user"):
                st.markdown(user_q)
            with st.chat_message("assistant"):
                with st.spinner("Thinking…"):
                    chat = ChatAgent(groq_key)
                    context_md = to_markdown(report)
                    answer = chat.reply(context_md, st.session_state.chat_history[:-1], user_q)
                    st.markdown(answer)
            st.session_state.chat_history.append({"role": "assistant", "content": answer})

    # ── Downloads ─────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📥 Download Report")
    d1, d2, d3 = st.columns(3)
    md_text = to_markdown(report)
    pdf_bytes = to_pdf(report)
    fname = company.replace(" ", "_")
    with d1:
        st.download_button("📄 Markdown (.md)", data=md_text.encode("utf-8"),
                           file_name=f"{fname}_report.md",
                           mime="text/markdown", use_container_width=True)
    with d2:
        st.download_button("📕 PDF (.pdf)", data=pdf_bytes,
                           file_name=f"{fname}_report.pdf",
                           mime="application/pdf", use_container_width=True)
    with d3:
        import json as _json
        st.download_button("🧾 JSON (.json)",
                           data=_json.dumps(
                               {k: v for k, v in report.items() if k != "raw_bundle"},
                               indent=2, default=str).encode("utf-8"),
                           file_name=f"{fname}_report.json",
                           mime="application/json", use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# Main render
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.report:
    render_report(st.session_state.report)
else:
    st.markdown("""
    <div class="card" style='text-align:center; padding:50px 30px;'>
      <div style='font-size:3rem; margin-bottom:10px;'>🔍</div>
      <h2 style='border:none; padding:0;'>Enter a company name above to begin</h2>
      <p style='color:#9ca3af; max-width:620px; margin:10px auto;'>
        The agent will run live web research across 8 queries, analyze the company,
        identify business challenges with impact analysis, map AI opportunities with priority scoring,
        and draft a personalized one-page CEO pitch — all in under a minute.
      </p>
      <p style='color:#6b7280; font-size:0.9rem; margin-top:16px;'>
        Evaluated on: Problem Solving &amp; Reasoning · Research Quality · Practical Recommendations · AI Tool Usage
      </p>
    </div>
    """, unsafe_allow_html=True)


st.markdown(f"""
<div class="footer">
  Powered by Groq Llama 3.3 + Tavily AI ·
  © {datetime.now().year}
</div>
""", unsafe_allow_html=True)
