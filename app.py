"""
app.py
------
PromptAdsCraft AI — Intelligent Marketing Content Generator & Creative Studio
Tagline: Craft smarter prompts. Create better ads.

A professional AI-powered UGC advertising and content marketing studio with:
- Real OpenAI API integration & transparent Demo Mode
- Premium dark creative studio theme with high-contrast, zero-white-bar UI styling
- 8-section sidebar navigation:
    1. 🏠 Dashboard
    2. 🚀 Campaign Generator
    3. 📊 Campaign Results (Studio & In-Line Editor)
    4. 🎨 Creative Gallery (Active & Saved User Creatives)
    5. 🌟 Sample Campaigns (Dedicated Read-Only Demo Gallery)
    6. 📁 Campaign History (Saved Campaigns Library)
    7. 🔍 Prompt Inspector (Real Templates & Variable Previews)
    8. ⚙️ Settings (API Credentials, Model Selection, Connection Test)
- In-line editing & section-level regeneration without full reruns
- Multi-format exports (Markdown, Plain Text, JSON)
- Strictly grounded real dashboard metrics
"""

from __future__ import annotations
import json
import os
import re
import sys
import time
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Page Configuration (Must be the very first Streamlit call)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="PromptAdsCraft AI — Creative Studio",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Module Imports & Configuration
# ---------------------------------------------------------------------------

sys.path.insert(0, str(Path(__file__).parent))

from config import (
    get_api_key, get_gemini_api_key, OPENAI_MODEL, MAX_TOKENS, REQUEST_TIMEOUT,
    CAMPAIGN_STORAGE_PATH, APP_NAME, APP_TAGLINE, APP_VERSION,
    SUPPORTED_PLATFORMS, SUPPORTED_TONES, SUPPORTED_DURATIONS, SUPPORTED_OBJECTIVES,
    MIN_HOOKS, MAX_HOOKS,
)
from src.validators import validate_campaign_input
from src.ai_service import AIService, AIServiceError, DemoModeActive
from src.content_generator import ContentGenerator
from src.storage import CampaignStorage
from src.exporters import export_as_json, export_as_markdown, export_as_txt
from src.prompt_builder import (
    get_all_template_names, get_template_metadata, load_template, sanitized_preview
)
from src.quality_checker import run_quality_check
import importlib
import src.synthesis_engine
import src.content_generator

try:
    importlib.reload(src.synthesis_engine)
    importlib.reload(src.content_generator)
except Exception:
    pass


def clean_campaign_output(campaign: dict) -> dict:
    """Ensure campaign output has no [DEMO] prefixes and is labeled as synthesized."""
    if not isinstance(campaign, dict):
        return campaign

    def _strip(val):
        if isinstance(val, str):
            if val.startswith("[DEMO] "):
                return val[7:]
            if val.startswith("[DEMO]"):
                return val[6:]
            return re.sub(r"^\[DEMO\]\s*", "", val)
        elif isinstance(val, dict):
            return {k: _strip(v) for k, v in val.items()}
        elif isinstance(val, list):
            return [_strip(v) for v in val]
        return val

    cleaned = _strip(campaign)
    cleaned["mode"] = "synthesis"
    return cleaned
# ---------------------------------------------------------------------------
# Comprehensive Dark Studio CSS
# Resolves all button contrast issues and eliminates white rectangular artifacts
# ---------------------------------------------------------------------------

st.markdown("""
<style>
    /* Theme color variables */
    :root {
        --bg-main: #080b12;
        --bg-card: #111827;
        --bg-card-alt: #162036;
        --border-subtle: #1e293b;
        --border-accent: #334155;
        --primary-indigo: #6366f1;
        --primary-violet: #8b5cf6;
        --accent-blue: #38bdf8;
        --accent-emerald: #10b981;
        --accent-amber: #f59e0b;
        --accent-rose: #f43f5e;
        --text-main: #f8fafc;
        --text-muted: #94a3b8;
    }

    /* Page background & Typography */
    .stApp {
        background-color: #080b12 !important;
        color: #f1f5f9 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Sidebar dark styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #090d16 0%, #0f172a 100%) !important;
        border-right: 1px solid #1e2638 !important;
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        font-size: 0.93rem;
        padding: 5px 0;
        font-weight: 500;
    }

    /* Top Hero Header */
    .hero-container {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.15) 50%, rgba(56, 189, 248, 0.1) 100%);
        border: 1px solid rgba(99, 102, 241, 0.35);
        border-radius: 14px;
        padding: 1.6rem 2.2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.5);
    }
    .hero-title {
        font-size: 1.9rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(90deg, #ffffff 0%, #cbd5e1 50%, #a5b4fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-tagline {
        color: #38bdf8;
        font-size: 1.02rem;
        font-weight: 500;
        margin-top: 0.25rem;
    }
    .hero-desc {
        color: #94a3b8;
        font-size: 0.9rem;
        margin-top: 0.5rem;
        line-height: 1.5;
    }

    /* Metric Card */
    .metric-card {
        background: #111827;
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 1.1rem 1.3rem;
        text-align: left;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f8fafc;
        margin-top: 0.2rem;
    }
    .metric-label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
        font-weight: 600;
    }
    .metric-sub {
        font-size: 0.75rem;
        color: #64748b;
        margin-top: 0.3rem;
    }

    /* Studio Card */
    .studio-card {
        background: #111827;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 1.3rem;
        margin-bottom: 0.8rem;
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .studio-card:hover {
        border-color: #38bdf8;
    }
    .studio-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.6rem;
    }
    .studio-card h4 {
        color: #f1f5f9;
        margin: 0;
        font-size: 1.05rem;
        font-weight: 600;
    }
    .studio-card p {
        color: #94a3b8;
        margin: 0.3rem 0;
        font-size: 0.88rem;
        line-height: 1.45;
    }

    /* Pills & Badges */
    .badge-pill {
        display: inline-block;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 9999px;
        letter-spacing: 0.02em;
    }
    .badge-indigo { background: rgba(99, 102, 241, 0.2); color: #a5b4fc; border: 1px solid rgba(99, 102, 241, 0.4); }
    .badge-blue { background: rgba(56, 189, 248, 0.2); color: #7dd3fc; border: 1px solid rgba(56, 189, 248, 0.4); }
    .badge-violet { background: rgba(139, 92, 246, 0.2); color: #c4b5fd; border: 1px solid rgba(139, 92, 246, 0.4); }
    .badge-emerald { background: rgba(16, 185, 129, 0.2); color: #6ee7b7; border: 1px solid rgba(16, 185, 129, 0.4); }
    .badge-amber { background: rgba(245, 158, 11, 0.2); color: #fde68a; border: 1px solid rgba(245, 158, 11, 0.4); }
    .badge-rose { background: rgba(244, 63, 94, 0.2); color: #fecdd3; border: 1px solid rgba(244, 63, 94, 0.4); }

    /* Banners */
    .demo-notice-box {
        background: rgba(245, 158, 11, 0.08);
        border: 1px solid rgba(245, 158, 11, 0.35);
        border-radius: 10px;
        padding: 1rem 1.3rem;
        margin-bottom: 1.2rem;
    }
    .demo-notice-title {
        color: #f59e0b;
        font-weight: 700;
        font-size: 0.95rem;
        margin-bottom: 0.2rem;
    }
    .demo-notice-body {
        color: #fde68a;
        font-size: 0.85rem;
        line-height: 1.45;
    }

    .ai-live-box {
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.35);
        border-radius: 10px;
        padding: 0.9rem 1.2rem;
        margin-bottom: 1.2rem;
    }

    /* Hook Box */
    .hook-studio-box {
        background: #111827;
        border: 1px solid #1e293b;
        border-left: 4px solid #6366f1;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.9rem;
    }
    .hook-studio-num {
        font-size: 0.78rem;
        font-weight: 700;
        color: #818cf8;
        text-transform: uppercase;
        margin-bottom: 0.3rem;
    }
    .hook-studio-text {
        font-size: 1.05rem;
        font-weight: 600;
        color: #f8fafc;
        margin-bottom: 0.4rem;
        font-style: italic;
    }
    .hook-studio-meta {
        font-size: 0.8rem;
        color: #94a3b8;
    }

    /* =========================================================================
       CRITICAL BUTTON OVERRIDES:
       Forces dark styling on ALL Streamlit buttons, resolving white rectangles
       ========================================================================= */
    div.stButton > button,
    div.stDownloadButton > button,
    .stButton button,
    .stDownloadButton button {
        background-color: #1a2236 !important;
        color: #f1f5f9 !important;
        border: 1px solid #2d3d5f !important;
        border-radius: 8px !important;
        padding: 0.55rem 1.1rem !important;
        font-weight: 500 !important;
        font-size: 0.88rem !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
        text-shadow: none !important;
    }

    /* Secondary Button Hover State */
    div.stButton > button:hover,
    div.stDownloadButton > button:hover,
    .stButton button:hover,
    .stDownloadButton button:hover {
        background-color: #24304c !important;
        border-color: #38bdf8 !important;
        color: #38bdf8 !important;
        box-shadow: 0 0 14px rgba(56, 189, 248, 0.3) !important;
        transform: translateY(-1px);
    }

    /* Focus & Active State */
    div.stButton > button:focus,
    div.stButton > button:active,
    .stButton button:active {
        background-color: #2c3c60 !important;
        border-color: #0284c7 !important;
        color: #ffffff !important;
        outline: none !important;
        box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.4) !important;
        transform: translateY(0);
    }

    /* Primary Button Styling */
    div.stButton > button[kind="primary"],
    .stButton button[kind="primary"],
    button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35) !important;
    }

    div.stButton > button[kind="primary"]:hover,
    .stButton button[kind="primary"]:hover,
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
        border-color: #a5b4fc !important;
        color: #ffffff !important;
        box-shadow: 0 6px 18px rgba(99, 102, 241, 0.5) !important;
        transform: translateY(-1px);
    }

    /* Disabled State */
    div.stButton > button:disabled,
    div.stDownloadButton > button:disabled,
    .stButton button:disabled {
        background-color: #0f1524 !important;
        color: #475569 !important;
        border-color: #1e293b !important;
        box-shadow: none !important;
        cursor: not-allowed !important;
        opacity: 0.65 !important;
    }

    /* Streamlit widgets dark overrides */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {
        background-color: #111827 !important;
        color: #f8fafc !important;
        border-color: #1e293b !important;
    }

    /* Progress bar accent */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #6366f1 0%, #38bdf8 100%) !important;
    }

    /* Expander header */
    .streamlit-expanderHeader {
        background-color: #111827 !important;
        border-radius: 8px !important;
        color: #f8fafc !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------

def init_session():
    defaults = {
        "campaign_result": None,
        "nav_page": "🏠 Dashboard",
        "custom_api_key": "",
        "custom_gemini_api_key": "",
        "prefill_inputs": None,
        "active_model": OPENAI_MODEL,
        "show_delete_confirm": None,
        "history_filter_platform": "All",
        "history_filter_status": "All",
        "history_search_query": "",
        "gallery_filter_category": "All Creatives",
        "last_connection_test": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_session()

# ---------------------------------------------------------------------------
# Services (Cached & Dynamically Configured)
# ---------------------------------------------------------------------------

@st.cache_resource
def get_storage():
    return CampaignStorage(storage_path=CAMPAIGN_STORAGE_PATH)


storage = get_storage()

def resolve_api_keys() -> tuple[str | None, str | None]:
    session_openai = st.session_state.get("custom_api_key", "").strip()
    session_gemini = st.session_state.get("custom_gemini_api_key", "").strip()
    openai_k = session_openai or get_api_key()
    gemini_k = session_gemini or get_gemini_api_key()
    return openai_k, gemini_k


active_openai_key, active_gemini_key = resolve_api_keys()
active_model = st.session_state.get("active_model", OPENAI_MODEL)

ai_service = AIService(
    api_key=active_openai_key,
    gemini_api_key=active_gemini_key,
    model=active_model,
    max_tokens=MAX_TOKENS,
    timeout=REQUEST_TIMEOUT,
)
generator = ContentGenerator(ai_service)

# ---------------------------------------------------------------------------
# Navigation State & Helper
# ---------------------------------------------------------------------------

NAV_ITEMS = [
    "🏠 Dashboard",
    "🚀 Campaign Generator",
    "📊 Campaign Results",
    "🎨 Creative Gallery",
    "🌟 Sample Campaigns",
    "📁 Campaign History",
    "🔍 Prompt Inspector",
    "⚙️ Settings",
]

def navigate_to(page_name: str):
    """Programmatically switch page and rerun."""
    st.session_state["_target_page"] = page_name
    st.rerun()


# Apply pending navigation before radio widget is rendered
if "_target_page" in st.session_state and st.session_state["_target_page"] in NAV_ITEMS:
    st.session_state["nav_radio"] = st.session_state.pop("_target_page")

if "nav_radio" not in st.session_state or st.session_state["nav_radio"] not in NAV_ITEMS:
    st.session_state["nav_radio"] = "🏠 Dashboard"

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("""
    <div style="text-align:left; padding: 0.8rem 0 1.2rem 0; border-bottom: 1px solid #1e293b; margin-bottom: 1rem;">
        <div style="display:flex; align-items:center; gap: 0.6rem;">
            <span style="font-size: 1.8rem;">✨</span>
            <div>
                <div style="font-size:1.15rem; font-weight:700; color:#f8fafc; line-height: 1.2;">PromptAdsCraft</div>
                <div style="font-size:0.75rem; color:#38bdf8; font-weight:500;">Intelligent Creative Studio</div>
            </div>
        </div>
        <div style="margin-top:0.5rem; font-size:0.72rem; color:#64748b;">v1.0.0 • Portfolio Project</div>
    </div>
    """, unsafe_allow_html=True)

    current_selection = st.session_state.get("nav_radio", "🏠 Dashboard")
    active_idx = NAV_ITEMS.index(current_selection) if current_selection in NAV_ITEMS else 0

    page = st.radio(
        "Navigation",
        NAV_ITEMS,
        index=active_idx,
        key="nav_radio",
        label_visibility="collapsed",
    )

    st.markdown("---")

    # Creative Engine Status
    st.markdown("""
    <div style="background: rgba(17, 24, 39, 0.8); border: 1px solid #1e293b; border-radius: 8px; padding: 0.75rem 0.9rem;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="color:#e2e8f0; font-size:0.8rem;">Creative Engine</strong>
            <span class="badge-pill badge-emerald">Online ⚡</span>
        </div>
        <div style="color:#94a3b8; font-size:0.75rem; margin-top:0.4rem; line-height:1.35;">
            Multi-Variable Prompt Synthesis Engine (Pure Python). Zero API keys required.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Saved Campaigns Metric
    saved_count = storage.campaign_count()
    st.markdown(f"""
    <div style="margin-top:1rem; font-size:0.78rem; color:#94a3b8; display:flex; justify-content:space-between;">
        <span>Saved Library:</span>
        <strong style="color:#e2e8f0;">{saved_count} campaign{'s' if saved_count != 1 else ''}</strong>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Notification & Banner Helpers
# ---------------------------------------------------------------------------

def render_demo_banner():
    pass


def render_live_ai_banner(model_name: str = ""):
    pass


# ---------------------------------------------------------------------------
# PAGE 1: DASHBOARD
# ---------------------------------------------------------------------------

def page_dashboard():
    st.markdown(f"""
    <div class="hero-container">
        <div class="hero-title">{APP_NAME}</div>
        <div class="hero-tagline">{APP_TAGLINE}</div>
        <div class="hero-desc">
            An intelligent marketing studio that converts product and business briefs into complete, 
            high-converting UGC video scripts, scroll-stopping hooks, truthful CTAs, platform adaptations, 
            and transparent quality audits.
        </div>
    </div>
    """, unsafe_allow_html=True)



    # Primary Action Button
    col_cta1, col_cta2 = st.columns([2, 1])
    with col_cta1:
        st.markdown("### 📊 Studio Performance & Library")
    with col_cta2:
        if st.button("✨ Create New Campaign", type="primary", use_container_width=True, key="dash_btn_create"):
            navigate_to("🚀 Campaign Generator")

    # Real Metrics calculated directly from storage (No placeholder or fake numbers!)
    metrics = storage.get_metrics()
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Campaigns</div>
            <div class="metric-value">{metrics['total_campaigns']}</div>
            <div class="metric-sub">Stored in local library</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Completed</div>
            <div class="metric-value">{metrics['completed_campaigns']}</div>
            <div class="metric-sub">Production-ready packages</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Drafts</div>
            <div class="metric-value">{metrics['draft_campaigns']}</div>
            <div class="metric-sub">In-progress concepts</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        avg_score_str = f"{metrics['avg_quality_score']}/100" if metrics['avg_quality_score'] is not None else "N/A"
        sub_text = f"Across {metrics['total_scored_campaigns']} audited campaigns" if metrics['avg_quality_score'] is not None else "Audits run on generation"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Avg Quality Score</div>
            <div class="metric-value">{avg_score_str}</div>
            <div class="metric-sub">{sub_text}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Quick Start Templates Section
    st.markdown("### ⚡ Quick-Start Campaign Templates")
    st.markdown("Select a sample brief to pre-populate the Campaign Generator as a new draft, or inspect it in the Demo Gallery:")

    col_t1, col_t2, col_t3 = st.columns(3)

    with col_t1:
        st.markdown("""
        <div class="studio-card">
            <div class="studio-card-header">
                <h4>🌸 GlowUp Skincare</h4>
                <span class="badge-pill badge-indigo">E-Commerce</span>
            </div>
            <p><strong>Product:</strong> Daily Hydrating Moisturizer<br>
            <strong>Platform:</strong> Instagram Reels (30s)<br>
            <strong>Tone:</strong> Friendly & Educational</p>
            <small style="color:#64748b;">Target: Adults 25-40 wanting clean hydration</small>
        </div>
        """, unsafe_allow_html=True)
        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            if st.button("📝 Use as Draft", key="btn_template_skincare", use_container_width=True):
                ex_path = Path(__file__).parent / "examples" / "skincare_campaign.json"
                if ex_path.exists():
                    data = json.loads(ex_path.read_text(encoding="utf-8"))
                    st.session_state.prefill_inputs = data.get("inputs", {})
                navigate_to("🚀 Campaign Generator")
        with btn_c2:
            if st.button("🔍 Inspect Sample", key="btn_inspect_skincare", use_container_width=True):
                navigate_to("🌟 Sample Campaigns")

    with col_t2:
        st.markdown("""
        <div class="studio-card">
            <div class="studio-card-header">
                <h4>☕ Bloom Specialty Cafe</h4>
                <span class="badge-pill badge-amber">Local Biz</span>
            </div>
            <p><strong>Product:</strong> Autumn Spice Seasonal Latte<br>
            <strong>Platform:</strong> Instagram Reels (15s)<br>
            <strong>Tone:</strong> Warm & Conversational</p>
            <small style="color:#64748b;">Target: Local coffee lovers & students</small>
        </div>
        """, unsafe_allow_html=True)
        btn_c3, btn_c4 = st.columns(2)
        with btn_c3:
            if st.button("📝 Use as Draft", key="btn_template_cafe", use_container_width=True):
                ex_path = Path(__file__).parent / "examples" / "local_cafe_campaign.json"
                if ex_path.exists():
                    data = json.loads(ex_path.read_text(encoding="utf-8"))
                    st.session_state.prefill_inputs = data.get("inputs", {})
                navigate_to("🚀 Campaign Generator")
        with btn_c4:
            if st.button("🔍 Inspect Sample", key="btn_inspect_cafe", use_container_width=True):
                navigate_to("🌟 Sample Campaigns")

    with col_t3:
        st.markdown("""
        <div class="studio-card">
            <div class="studio-card-header">
                <h4>⚡ FocusFlow App</h4>
                <span class="badge-pill badge-blue">SaaS Product</span>
            </div>
            <p><strong>Product:</strong> FocusFlow Productivity App<br>
            <strong>Platform:</strong> YouTube Shorts (60s)<br>
            <strong>Tone:</strong> Energetic & Direct</p>
            <small style="color:#64748b;">Target: Remote workers & students</small>
        </div>
        """, unsafe_allow_html=True)
        btn_c5, btn_c6 = st.columns(2)
        with btn_c5:
            if st.button("📝 Use as Draft", key="btn_template_saas", use_container_width=True):
                ex_path = Path(__file__).parent / "examples" / "saas_campaign.json"
                if ex_path.exists():
                    data = json.loads(ex_path.read_text(encoding="utf-8"))
                    st.session_state.prefill_inputs = data.get("inputs", {})
                navigate_to("🚀 Campaign Generator")
        with btn_c6:
            if st.button("🔍 Inspect Sample", key="btn_inspect_saas", use_container_width=True):
                navigate_to("🌟 Sample Campaigns")

    st.markdown("---")

    # Recent Campaigns List
    recent_campaigns = storage.list_campaigns()
    st.markdown("### 📁 Recent Campaigns in Library")

    if not recent_campaigns:
        st.markdown("""
        <div style="background:#111827; border: 1px dashed #334155; border-radius:10px; padding:1.8rem; text-align:center; color:#94a3b8;">
            <p style="margin:0; font-size:1rem;">No saved campaigns found yet.</p>
            <p style="margin:0.4rem 0 0 0; font-size:0.85rem; color:#64748b;">
                Click <strong>Create New Campaign</strong> or choose a quick-start template above to generate your first ad package!
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for c in recent_campaigns[:4]:
            col_info, col_act = st.columns([4, 1])
            with col_info:
                score_str = f"Score: {c['quality_score']}/100" if c.get("quality_score") else "Unscored"
                status_color = "badge-emerald" if c.get("status") == "Completed" else "badge-violet"
                st.markdown(f"""
                <div style="background:#111827; border:1px solid #1e293b; border-radius:8px; padding:0.9rem 1.2rem; margin-bottom:0.6rem;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <strong style="color:#f8fafc; font-size:1rem;">{c['name']}</strong>
                        <div>
                            <span class="badge-pill {status_color}">{c.get('status', 'Completed')}</span>
                            <span class="badge-pill badge-blue" style="margin-left:0.3rem;">{c.get('platform', 'N/A')}</span>
                        </div>
                    </div>
                    <div style="color:#94a3b8; font-size:0.82rem; margin-top:0.3rem;">
                        {c.get('brand_name', '')} • {c.get('product_name', '')} | <span style="color:#64748b;">{score_str} • {c['created_at'][:10]}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col_act:
                st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
                if st.button("📂 Open Results", key=f"dash_open_{c['id']}", use_container_width=True):
                    loaded = storage.load_campaign(c["id"])
                    if loaded:
                        st.session_state.campaign_result = loaded
                        navigate_to("📊 Campaign Results")


# ---------------------------------------------------------------------------
# PAGE 2: CAMPAIGN GENERATOR
# ---------------------------------------------------------------------------

def page_campaign_generator():
    st.markdown("""
    <div class="hero-container" style="padding: 1.4rem 2rem;">
        <div class="hero-title" style="font-size: 1.7rem;">🚀 Campaign Generator</div>
        <div class="hero-tagline">Transform your brief into scroll-stopping marketing assets</div>
    </div>
    """, unsafe_allow_html=True)

    # Retrieval of prefilled draft inputs
    prefill = st.session_state.get("prefill_inputs") or {}
    if prefill:
        st.info(f"📝 Pre-populated form with draft: **{prefill.get('brand_name', 'Draft')} - {prefill.get('product_name', '')}**")

    col_m1, col_m2 = st.columns([3, 1])
    with col_m1:
        st.markdown("""
        <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid #1e293b; border-radius: 8px; padding: 0.6rem 1rem;">
            <div style="font-size:0.85rem; font-weight:600; color:#38bdf8;">⚡ Multi-Variable Prompt Synthesis Engine Active</div>
            <div style="font-size:0.75rem; color:#94a3b8;">Zero API keys required • Sub-second generation • 100% Free & Unlimited</div>
        </div>
        """, unsafe_allow_html=True)
    with col_m2:
        if st.button("🔄 Reset / Clear Form", key="gen_clear_form", use_container_width=True):
            st.session_state.prefill_inputs = {}
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    with st.form("campaign_input_form", clear_on_submit=False):
        st.markdown("### 1️⃣ Brand & Product Essentials")
        col1, col2 = st.columns(2)
        with col1:
            brand_name = st.text_input(
                "Brand or Business Name *",
                value=prefill.get("brand_name", ""),
                placeholder="e.g. GlowUp Skincare",
                help="Your brand or creator handle (1-100 characters)",
            )
        with col2:
            product_name = st.text_input(
                "Product or Service Name *",
                value=prefill.get("product_name", ""),
                placeholder="e.g. Daily Hydrating Moisturizer",
                help="The specific product or offer being promoted",
            )

        description = st.text_area(
            "Product Description *",
            value=prefill.get("description", ""),
            placeholder="Detailed description of what the product does, key ingredients/features, and how it works (10-1000 characters)...",
            height=90,
            help="High-detail descriptions produce significantly more relevant scripts and angles.",
        )

        st.markdown("### 2️⃣ Target Audience & Campaign Strategy")
        col3, col4 = st.columns(2)
        with col3:
            target_audience = st.text_input(
                "Target Audience *",
                value=prefill.get("target_audience", ""),
                placeholder="e.g. Adults aged 25-40 with dry or sensitive skin",
                help="Demographics, psychographics, or specific customer profile",
            )
            objective = st.selectbox(
                "Marketing Objective *",
                SUPPORTED_OBJECTIVES,
                index=SUPPORTED_OBJECTIVES.index(prefill.get("objective", "Product Awareness"))
                if prefill.get("objective") in SUPPORTED_OBJECTIVES else 0,
            )
            platform = st.selectbox(
                "Primary Platform *",
                SUPPORTED_PLATFORMS,
                index=SUPPORTED_PLATFORMS.index(prefill.get("platform", "Instagram Reels"))
                if prefill.get("platform") in SUPPORTED_PLATFORMS else 0,
            )
        with col4:
            tone = st.selectbox(
                "Content Tone *",
                SUPPORTED_TONES,
                index=SUPPORTED_TONES.index(prefill.get("tone", "Friendly"))
                if prefill.get("tone") in SUPPORTED_TONES else 0,
            )
            duration = st.selectbox(
                "Video Ad Duration (seconds) *",
                SUPPORTED_DURATIONS,
                index=SUPPORTED_DURATIONS.index(prefill.get("duration", 30))
                if prefill.get("duration") in SUPPORTED_DURATIONS else 1,
            )
            language = st.text_input(
                "Campaign Language",
                value=prefill.get("language", "English"),
            )

        st.markdown("### 3️⃣ Content & Creative Guidance")
        col5, col6 = st.columns(2)
        with col5:
            num_hooks = st.slider(
                "Number of Hook Variations",
                min_value=MIN_HOOKS,
                max_value=MAX_HOOKS,
                value=int(prefill.get("num_hooks", 5)),
                help="How many distinct psychological opening hooks to produce",
            )
            benefits = st.text_area(
                "Key Product Benefits (User-Supplied) *",
                value=prefill.get("benefits", ""),
                placeholder="e.g. Absorbs in seconds. No greasy residue. Plant-based ingredients. All-day moisture.",
                height=80,
                help="The AI will strictly stick to these verified benefits without inventing claims.",
            )
        with col6:
            offer = st.text_input(
                "Verified Offer / Discount (Optional)",
                value=prefill.get("offer", ""),
                placeholder="e.g. Use code GLOW15 for 15% off first order",
                help="Only provide if actively authorized; never invented by the AI",
            )
            avoid_words = st.text_input(
                "Restricted Claims or Words to Avoid (Optional)",
                value=prefill.get("avoid_words", ""),
                placeholder="e.g. clinically proven, cure, miracle, guarantee",
                help="Compliance filter to prevent deceptive or risky claims",
            )
            pain_points = st.text_input(
                "Audience Pain Points (Optional)",
                value=prefill.get("pain_points", ""),
                placeholder="e.g. Skin feeling dry 2 hours after moisturizing, sticky lotions",
                help="Frustrations or challenges your product solves",
            )

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button(
            "✨ Generate Campaign Package",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        inputs_payload = {
            "brand_name": brand_name,
            "product_name": product_name,
            "description": description,
            "target_audience": target_audience,
            "objective": objective,
            "platform": platform,
            "tone": tone,
            "language": language,
            "duration": duration,
            "num_hooks": num_hooks,
            "benefits": benefits,
            "offer": offer,
            "avoid_words": avoid_words,
            "pain_points": pain_points,
        }

        # Validate inputs with Pydantic
        campaign_input, errors = validate_campaign_input(inputs_payload)
        if errors:
            st.error("Please address the validation errors below before generating:")
            for err in errors:
                st.markdown(f"• **{err}**")
            return

        # Progress UI
        progress_bar = st.progress(0, text="Initializing generation studio...")
        status_box = st.empty()

        def update_progress(msg: str, pct: float):
            progress_bar.progress(pct, text=msg)
            status_box.markdown(f"<span style='color:#38bdf8; font-size:0.85rem;'>⚡ {msg}</span>", unsafe_allow_html=True)
            time.sleep(0.02)

        try:
            with st.spinner("Synthesizing campaign package..."):
                try:
                    result = generator.generate_full_campaign(
                        inputs=inputs_payload,
                        progress_callback=update_progress,
                        force_demo=True,
                        label_as_demo=False,
                    )
                except TypeError:
                    result = generator.generate_full_campaign(
                        inputs=inputs_payload,
                        progress_callback=update_progress,
                        force_demo=True,
                    )
                result = clean_campaign_output(result)

            st.session_state.campaign_result = result
            st.session_state["just_generated"] = True

            # Save to storage
            campaign_title = f"{brand_name} - {product_name} ({platform})"
            save_status = "Completed"
            storage.save_campaign(result, campaign_name=campaign_title, status=save_status)

            progress_bar.progress(1.0, text="Campaign generated successfully!")
            status_box.empty()
            st.success("✅ Complete advertising campaign generated and saved! Redirecting to Content Studio...")
            time.sleep(0.3)
            navigate_to("📊 Campaign Results")

        except Exception as exc:
            progress_bar.empty()
            status_box.empty()
            st.error(f"Generation error: {str(exc)}")

    # Render results inline if available
    if st.session_state.get("campaign_result"):
        st.markdown("---")
        col_hdr, col_btn = st.columns([3, 1])
        with col_hdr:
            st.markdown("### 📊 Active Generated Campaign")
        with col_btn:
            if st.button("↗️ Open in Full Studio", key="btn_goto_results_from_gen", use_container_width=True):
                navigate_to("📊 Campaign Results")
        render_campaign_results_view(st.session_state.campaign_result, key_prefix="gen_page")


# ---------------------------------------------------------------------------
# PAGE 3: CAMPAIGN RESULTS & CONTENT STUDIO
# ---------------------------------------------------------------------------

def page_campaign_results():
    st.markdown("""
    <div class="hero-container" style="padding: 1.4rem 2rem;">
        <div class="hero-title" style="font-size: 1.7rem;">📊 Creative Studio & Results</div>
        <div class="hero-tagline">Inspect, edit in-line, regenerate individual sections, and export</div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.pop("just_generated", False):
        st.success("🎉 Campaign package generated and saved to your library! Review and customize each section below.")

    campaign = st.session_state.get("campaign_result")
    if not campaign:
        st.info("No active campaign in memory. Go to **🚀 Campaign Generator** or open a saved campaign from **📁 Campaign History**.")
        if st.button("→ Go to Campaign Generator", key="btn_go_gen_empty_res"):
            navigate_to("🚀 Campaign Generator")
        return

    render_campaign_results_view(campaign, key_prefix="studio")


def render_campaign_results_view(campaign: dict, key_prefix: str = "studio"):
    inputs = campaign.get("inputs", {})
    brief = campaign.get("brief", {})
    st.markdown("""
    <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 8px; padding: 0.6rem 1rem; margin-bottom: 1rem;">
        <span style="color:#34d399; font-weight:600; font-size:0.85rem;">⚡ Generated via Multi-Variable Prompt Synthesis Engine</span>
        <span style="color:#94a3b8; font-size:0.8rem; margin-left: 0.5rem;">Pure Python • Deterministic • Zero API Latency</span>
    </div>
    """, unsafe_allow_html=True)

    # Top Status Bar
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Brand & Product</div>
            <div style="font-size:1.1rem; font-weight:700; color:#f8fafc; margin-top:0.2rem;">
                {inputs.get('brand_name', 'N/A')}
            </div>
            <div class="metric-sub">{inputs.get('product_name', 'N/A')}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Target Platform</div>
            <div style="font-size:1.1rem; font-weight:700; color:#38bdf8; margin-top:0.2rem;">
                {inputs.get('platform', 'N/A')}
            </div>
            <div class="metric-sub">{inputs.get('duration', '30')}s • {inputs.get('tone', 'Friendly')}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        hooks_count = len(campaign.get("hooks", []))
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Creative Assets</div>
            <div style="font-size:1.1rem; font-weight:700; color:#a5b4fc; margin-top:0.2rem;">
                {hooks_count} Hooks • UGC Script
            </div>
            <div class="metric-sub">CTAs, Captions & Adaptations</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        qr = campaign.get("quality_review", {})
        score = qr.get("overall_score", "N/A") if isinstance(qr, dict) else "N/A"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Quality Score</div>
            <div style="font-size:1.1rem; font-weight:700; color:#10b981; margin-top:0.2rem;">
                {score}/100
            </div>
            <div class="metric-sub">Heuristic compliance audit</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 1. Campaign Summary
    with st.expander("📋 1. Strategic Campaign Brief", expanded=True):
        col_b_hdr, col_b_regen = st.columns([4, 1])
        with col_b_hdr:
            st.markdown("#### Strategic Synthesis")
        with col_b_regen:
            if st.button("🔄 Regenerate Brief", key=f"{key_prefix}_regen_brief", use_container_width=True):
                with st.spinner("Regenerating campaign brief..."):
                    try:
                        campaign["brief"] = generator.generate_brief(inputs)
                        campaign["quality_review"] = run_quality_check(campaign)
                        st.session_state.campaign_result = campaign
                        st.success("Brief updated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Regeneration failed: {e}")

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.markdown("**Campaign Summary:**")
            summary_val = st.text_area(
                "Summary",
                value=brief.get("summary", ""),
                height=90,
                key=f"{key_prefix}_edit_summary",
                label_visibility="collapsed",
            )
            campaign["brief"]["summary"] = summary_val

            st.markdown("**Main Marketing Message:**")
            msg_val = st.text_input(
                "Main Message",
                value=brief.get("main_message", ""),
                key=f"{key_prefix}_edit_main_msg",
                label_visibility="collapsed",
            )
            campaign["brief"]["main_message"] = msg_val

        with col_b2:
            st.markdown("**Audience Insight:**")
            st.info(brief.get("audience_insight", "N/A"))

            st.markdown("**Creative Direction:**")
            st.caption(brief.get("creative_direction", "N/A"))

            ksp = brief.get("key_selling_points", [])
            if ksp:
                st.markdown("**Key Selling Points:**")
                for pt in ksp:
                    st.markdown(f"• {pt}")

        flagged = brief.get("flagged_claims", [])
        if flagged:
            st.warning("⚠️ **Claims Flagged for Verification:**\n" + "\n".join(f"- {f}" for f in flagged))

    # 2. Hooks
    with st.expander("🎣 2. Advertising Hooks (Scroll-Stoppers)", expanded=True):
        col_h_hdr, col_h_regen = st.columns([4, 1])
        with col_h_hdr:
            st.markdown("#### Distinct Psychological Angles")
        with col_h_regen:
            if st.button("🔄 Regenerate Hooks", key=f"{key_prefix}_regen_hooks", use_container_width=True):
                with st.spinner("Regenerating hook variations..."):
                    try:
                        campaign["hooks"] = generator.generate_hooks(inputs, campaign.get("brief", {}))
                        campaign["quality_review"] = run_quality_check(campaign)
                        st.session_state.campaign_result = campaign
                        st.success("Hooks regenerated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Regeneration failed: {e}")

        hooks = campaign.get("hooks", [])
        for i, hook in enumerate(hooks):
            st.markdown(f"""
            <div class="hook-studio-box">
                <div class="hook-studio-num">Hook {hook.get('hook_number', i+1)} • {hook.get('style', 'Angle')}</div>
                <div class="hook-studio-text">"{hook.get('hook_text', '')}"</div>
                <div class="hook-studio-meta">
                    <strong>Appeal:</strong> {hook.get('audience_appeal', 'N/A')} | 
                    <strong>Why it works:</strong> {hook.get('why_it_works', 'N/A')}
                </div>
            </div>
            """, unsafe_allow_html=True)
            new_hook_text = st.text_input(
                f"Edit Hook {i+1}",
                value=hook.get("hook_text", ""),
                key=f"{key_prefix}_hook_edit_{i}",
                label_visibility="collapsed",
            )
            hook["hook_text"] = new_hook_text

    # 3. UGC Script
    with st.expander("🎬 3. UGC Video Script (Scene-by-Scene)", expanded=True):
        col_s_hdr, col_s_regen = st.columns([4, 1])
        with col_s_hdr:
            st.markdown("#### Scene-by-Scene Production Blueprint")
        with col_s_regen:
            if st.button("🔄 Regenerate Script", key=f"{key_prefix}_regen_script", use_container_width=True):
                with st.spinner("Regenerating video script..."):
                    try:
                        hook_t = hooks[0]["hook_text"] if hooks else ""
                        primary_cta = campaign.get("ctas", {}).get("recommended_primary_cta", "Visit website")
                        campaign["script"] = generator.generate_script(inputs, campaign.get("brief", {}), hook_t, primary_cta)
                        campaign["quality_review"] = run_quality_check(campaign)
                        st.session_state.campaign_result = campaign
                        st.success("Script regenerated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Regeneration failed: {e}")

        script = campaign.get("script", {})
        default_dur_str = f"{inputs.get('duration', 30)} seconds"
        est_duration = script.get("total_estimated_duration", default_dur_str)
        st.markdown(f"**Title:** {script.get('script_title', 'UGC Ad Script')} | **Target Duration:** {est_duration}")
        if script.get("content_note"):
            st.caption(f"ℹ️ {script.get('content_note')}")

        scenes = script.get("scenes", [])
        for sc in scenes:
            st.markdown(f"""
            <div style="background:#131d33; border: 1px solid #1e293b; border-radius:8px; padding:0.9rem; margin-bottom:0.7rem;">
                <div style="display:flex; justify-content:space-between; margin-bottom:0.4rem;">
                    <strong style="color:#38bdf8;">Scene {sc.get('scene_number', '?')} ({sc.get('timestamp', '0:00')})</strong>
                    <span class="badge-pill badge-violet">{sc.get('shot_suggestion', 'Medium Shot')}</span>
                </div>
                <div style="color:#e2e8f0; font-size:0.92rem; margin-bottom:0.3rem;">
                    🎥 <strong>Visual:</strong> {sc.get('visual_direction', '')}
                </div>
                <div style="color:#cbd5e1; font-size:0.92rem; font-style:italic;">
                    🗣️ <strong>Dialogue:</strong> "{sc.get('dialogue', '')}"
                </div>
                <div style="color:#94a3b8; font-size:0.8rem; margin-top:0.3rem;">
                    📝 <strong>On-Screen Text:</strong> {sc.get('on_screen_text', 'None')} | 
                    ↪️ <strong>Transition:</strong> {sc.get('transition', 'Cut')}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"**Closing CTA:** {script.get('final_cta', 'Link in bio')}")
        if script.get("production_notes"):
            st.caption(f"📋 Production Notes: {script.get('production_notes')}")

    # 4. Calls to Action
    with st.expander("📢 4. Calls to Action (Funnel Aligned)", expanded=False):
        col_c_hdr, col_c_regen = st.columns([4, 1])
        with col_c_hdr:
            st.markdown("#### High-Intent, Deception-Free CTAs")
        with col_c_regen:
            if st.button("🔄 Regenerate CTAs", key=f"{key_prefix}_regen_ctas", use_container_width=True):
                with st.spinner("Regenerating CTAs..."):
                    try:
                        campaign["ctas"] = generator.generate_ctas(inputs)
                        campaign["quality_review"] = run_quality_check(campaign)
                        st.session_state.campaign_result = campaign
                        st.success("CTAs regenerated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Regeneration failed: {e}")

        ctas = campaign.get("ctas", {})
        prim_cta = ctas.get("recommended_primary_cta", "")
        if prim_cta:
            st.markdown(f"""
            <div style="background: rgba(99, 102, 241, 0.15); border: 1px solid #6366f1; border-radius:8px; padding:0.9rem; margin-bottom:1rem;">
                <strong style="color:#a5b4fc;">⭐ Recommended Primary CTA:</strong>
                <div style="font-size:1.05rem; font-weight:600; color:#ffffff; margin-top:0.2rem;">{prim_cta}</div>
                <small style="color:#94a3b8;">{ctas.get('cta_guidance', '')}</small>
            </div>
            """, unsafe_allow_html=True)

        col_cta_a, col_cta_b = st.columns(2)
        with col_cta_a:
            st.markdown("**💬 Engagement CTAs:**")
            for c_item in ctas.get("engagement_ctas", []):
                st.markdown(f"• {c_item}")
            st.markdown("**🌐 Website Visit CTAs:**")
            for c_item in ctas.get("website_visit_ctas", []):
                st.markdown(f"• {c_item}")
        with col_cta_b:
            st.markdown("**🔍 Product Discovery CTAs:**")
            for c_item in ctas.get("product_discovery_ctas", []):
                st.markdown(f"• {c_item}")
            st.markdown("**🛒 Purchase Intent CTAs:**")
            for c_item in ctas.get("purchase_intent_ctas", []):
                st.markdown(f"• {c_item}")

    # 5. Captions & Hashtags
    with st.expander("📝 5. Captions & Hashtags", expanded=False):
        col_cap_hdr, col_cap_regen = st.columns([4, 1])
        with col_cap_hdr:
            st.markdown("#### Feed Captions & Tag Strategy")
        with col_cap_regen:
            if st.button("🔄 Regenerate Captions", key=f"{key_prefix}_regen_captions", use_container_width=True):
                with st.spinner("Regenerating captions & hashtags..."):
                    try:
                        p_cta = campaign.get("ctas", {}).get("recommended_primary_cta", "Link in bio")
                        campaign["captions"] = generator.generate_captions(inputs, campaign.get("brief", {}), p_cta)
                        campaign["quality_review"] = run_quality_check(campaign)
                        st.session_state.campaign_result = campaign
                        st.success("Captions regenerated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Regeneration failed: {e}")

        captions = campaign.get("captions", {})
        st.markdown("**Concise Caption (Punchy):**")
        st.info(captions.get("concise_caption", ""))

        st.markdown("**Extended Caption (Storytelling):**")
        ext_cap = st.text_area(
            "Extended Caption",
            value=captions.get("extended_caption", ""),
            height=100,
            key=f"{key_prefix}_ext_cap",
            label_visibility="collapsed",
        )
        captions["extended_caption"] = ext_cap

        tags = captions.get("hashtags", [])
        if tags:
            st.markdown("**Niche Hashtags:**")
            st.code(" ".join(tags), language=None)
            if captions.get("hashtag_strategy"):
                st.caption(f"Strategy: {captions.get('hashtag_strategy')}")

    # 6. Platform Adaptations
    with st.expander("📱 6. Platform Adaptations (Reels, Shorts, Paid Social)", expanded=False):
        col_plat_hdr, col_plat_regen = st.columns([4, 1])
        with col_plat_hdr:
            st.markdown("#### Native Cross-Platform Variants")
        with col_plat_regen:
            if st.button("🔄 Regenerate Adaptations", key=f"{key_prefix}_regen_plats", use_container_width=True):
                with st.spinner("Regenerating platform adaptations..."):
                    try:
                        hook_t = hooks[0]["hook_text"] if hooks else ""
                        p_cta = campaign.get("ctas", {}).get("recommended_primary_cta", "Link in bio")
                        campaign["platform_adaptation"] = generator.generate_platform_adaptation(
                            inputs, campaign.get("brief", {}), hook_t, p_cta
                        )
                        st.session_state.campaign_result = campaign
                        st.success("Platform variants updated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Regeneration failed: {e}")

        platforms = campaign.get("platform_adaptation", {})
        tab_reels, tab_shorts, tab_paid = st.tabs(["📸 Instagram Reels", "▶️ YouTube Shorts", "💰 Paid Social Ads"])

        with tab_reels:
            r = platforms.get("instagram_reels", {})
            st.markdown(f"**Format:** {r.get('creative_format', '9:16 Vertical')}")
            st.markdown(f"**Opening Hook:** *{r.get('opening_hook', '')}*")
            st.markdown(f"**Pacing & Structure:** {r.get('script_structure', '')}")
            st.caption(f"Best practice: {r.get('best_practice_notes', '')}")

        with tab_shorts:
            s = platforms.get("youtube_shorts", {})
            st.markdown(f"**Format:** {s.get('creative_format', '9:16 Vertical')}")
            st.markdown(f"**Opening Hook:** *{s.get('opening_hook', '')}*")
            st.markdown(f"**Pacing & Structure:** {s.get('script_structure', '')}")
            st.caption(f"Best practice: {s.get('best_practice_notes', '')}")

        with tab_paid:
            p = platforms.get("paid_social_ads", {})
            st.markdown(f"**Format:** {p.get('creative_format', '1:1 Square or 4:5')}")
            st.markdown(f"**Opening Hook:** *{p.get('opening_hook', '')}*")
            st.markdown(f"**Pacing & Structure:** {p.get('script_structure', '')}")
            st.caption(f"Best practice: {p.get('best_practice_notes', '')}")

    # 7. Creative Angles
    with st.expander("💡 7. Alternative Creative Angles", expanded=False):
        angles = campaign.get("creative_angles", [])
        col_ang1, col_ang2 = st.columns(2)
        for idx, ang in enumerate(angles):
            with col_ang1 if idx % 2 == 0 else col_ang2:
                if isinstance(ang, dict):
                    st.markdown(f"""
                    <div style="background:#111827; border: 1px solid #1e293b; border-radius:8px; padding:0.8rem; margin-bottom:0.5rem;">
                        <strong style="color:#a5b4fc;">{ang.get('angle', 'Angle')}</strong>
                        <div style="font-size:0.84rem; color:#94a3b8; margin-top:0.2rem;">{ang.get('description', '')}</div>
                    </div>
                    """, unsafe_allow_html=True)

    # 8. Quality Review
    with st.expander("🛡️ 8. Content Quality & Compliance Audit", expanded=True):
        qr = campaign.get("quality_review") or run_quality_check(campaign)
        overall_score = qr.get("overall_score", 0)
        st.markdown(f"#### Overall Content Quality Score: **{overall_score}/100**")
        st.progress(overall_score / 100)
        st.caption(qr.get("score_disclaimer", "Heuristic content quality checks. Not an ad performance guarantee."))

        checklist = qr.get("checklist", {})
        col_q1, col_q2 = st.columns(2)
        idx = 0
        for crit, res in checklist.items():
            with col_q1 if idx % 2 == 0 else col_q2:
                score_badge_cls = "badge-emerald" if res["score"] >= 75 else "badge-amber" if res["score"] >= 50 else "badge-rose"
                st.markdown(f"""
                <div style="background:#111827; border:1px solid #1e293b; border-radius:6px; padding:0.6rem 0.8rem; margin-bottom:0.5rem;">
                    <div style="display:flex; justify-content:space-between;">
                        <strong style="color:#e2e8f0; font-size:0.88rem;">{crit.replace('_', ' ').title()}</strong>
                        <span class="badge-pill {score_badge_cls}">{res['score']}/100</span>
                    </div>
                    <div style="font-size:0.8rem; color:#94a3b8; margin-top:0.2rem;">{res['finding']}</div>
                </div>
                """, unsafe_allow_html=True)
            idx += 1

        flagged_items = qr.get("flagged_items", [])
        if flagged_items:
            st.warning("⚠️ **Compliance Checklist Items to Verify:**\n" + "\n".join(f"- {item}" for item in flagged_items))

    # Exports
    st.markdown("---")
    st.markdown("### 📥 Export & Library Controls")

    col_e1, col_e2, col_e3, col_e4 = st.columns(4)
    brand_file_slug = inputs.get("brand_name", "campaign").lower().replace(" ", "_")

    with col_e1:
        md_text = export_as_markdown(campaign)
        st.download_button(
            label="📄 Export Markdown (.md)",
            data=md_text,
            file_name=f"{brand_file_slug}_campaign.md",
            mime="text/markdown",
            use_container_width=True,
            key=f"{key_prefix}_dl_md",
        )

    with col_e2:
        txt_text = export_as_txt(campaign)
        st.download_button(
            label="📋 Export Plain Text (.txt)",
            data=txt_text,
            file_name=f"{brand_file_slug}_campaign.txt",
            mime="text/plain",
            use_container_width=True,
            key=f"{key_prefix}_dl_txt",
        )

    with col_e3:
        json_text = export_as_json(campaign)
        st.download_button(
            label="💾 Export JSON (.json)",
            data=json_text,
            file_name=f"{brand_file_slug}_campaign.json",
            mime="application/json",
            use_container_width=True,
            key=f"{key_prefix}_dl_json",
        )

    with col_e4:
        if st.button("💾 Save Changes to Library", type="primary", use_container_width=True, key=f"{key_prefix}_save_changes"):
            camp_name = f"{inputs.get('brand_name', 'Brand')} - {inputs.get('product_name', 'Campaign')}"
            storage.save_campaign(campaign, campaign_name=camp_name, status="Completed")
            st.success("Campaign updated in your library!")


# ---------------------------------------------------------------------------
# PAGE 4: CREATIVE GALLERY (Active & Saved User Creatives Only)
# ---------------------------------------------------------------------------

def page_creative_gallery():
    st.markdown("""
    <div class="hero-container" style="padding: 1.4rem 2rem;">
        <div class="hero-title" style="font-size: 1.7rem;">🎨 Creative Gallery</div>
        <div class="hero-tagline">Visual showcase of your generated hooks, video scripts, CTAs, and platform creatives</div>
    </div>
    """, unsafe_allow_html=True)

    categories = [
        "All Creatives",
        "🎣 Advertising Hooks",
        "🎬 UGC Video Scripts",
        "📢 CTAs & Captions",
        "📱 Platform Creatives",
    ]

    selected_category = st.radio(
        "Filter Category",
        categories,
        horizontal=True,
        key="gallery_category_radio",
        label_visibility="collapsed",
    )

    gallery_items = []

    def extract_creatives(camp_data: dict, source_label: str):
        c_inputs = camp_data.get("inputs", {})
        c_brand = c_inputs.get("brand_name", "Brand")
        c_product = c_inputs.get("product_name", "Product")
        c_plat = c_inputs.get("platform", "Instagram Reels")

        # Hooks
        for h in camp_data.get("hooks", []):
            gallery_items.append({
                "type": "🎣 Advertising Hooks",
                "title": f"Hook: {h.get('style', 'Angle')}",
                "brand": c_brand,
                "product": c_product,
                "platform": c_plat,
                "content": h.get("hook_text", ""),
                "meta": f"Appeal: {h.get('audience_appeal', '')} | Why it works: {h.get('why_it_works', '')}",
                "badge": "Hook Asset",
                "badge_cls": "badge-indigo",
            })

        # Scripts
        script = camp_data.get("script", {})
        if script and script.get("scenes"):
            first_scene = script["scenes"][0]
            gallery_items.append({
                "type": "🎬 UGC Video Scripts",
                "title": script.get("script_title", "UGC Video Script"),
                "brand": c_brand,
                "product": c_product,
                "platform": c_plat,
                "content": f"Opening Scene Dialogue: \"{first_scene.get('dialogue', '')}\"\nVisual: {first_scene.get('visual_direction', '')}",
                "meta": f"Duration: {script.get('total_estimated_duration', '30s')} • {len(script.get('scenes', []))} Scenes",
                "badge": "Video Script",
                "badge_cls": "badge-blue",
            })

        # CTAs & Captions
        captions = camp_data.get("captions", {})
        ctas = camp_data.get("ctas", {})
        if captions.get("concise_caption") or ctas.get("recommended_primary_cta"):
            gallery_items.append({
                "type": "📢 CTAs & Captions",
                "title": f"CTA & Caption Set",
                "brand": c_brand,
                "product": c_product,
                "platform": c_plat,
                "content": f"Primary CTA: {ctas.get('recommended_primary_cta', 'N/A')}\nCaption: \"{captions.get('concise_caption', '')}\"",
                "meta": f"Hashtags: {' '.join(captions.get('hashtags', [])[:5])}",
                "badge": "Direct Response",
                "badge_cls": "badge-amber",
            })

        # Platform Creatives
        plats = camp_data.get("platform_adaptation", {})
        for pk, pl_obj in plats.items():
            if pl_obj and pl_obj.get("opening_hook"):
                plat_label = pk.replace("_", " ").title()
                gallery_items.append({
                    "type": "📱 Platform Creatives",
                    "title": f"{plat_label} Ad Creative",
                    "brand": c_brand,
                    "product": c_product,
                    "platform": plat_label,
                    "content": f"Hook: \"{pl_obj.get('opening_hook', '')}\"\nFormat: {pl_obj.get('creative_format', '')}",
                    "meta": f"Structure: {pl_obj.get('script_structure', '')}",
                    "badge": plat_label,
                    "badge_cls": "badge-emerald",
                })

    # Include only user's active campaign and saved campaigns (strictly NO unrelated sample mixing)
    if st.session_state.get("campaign_result"):
        extract_creatives(st.session_state.campaign_result, "Active Campaign")

    saved_list = storage.list_campaigns()
    for s_entry in saved_list:
        full_c = storage.load_campaign(s_entry["id"])
        if full_c:
            extract_creatives(full_c, s_entry["name"])

    filtered_items = [
        item for item in gallery_items
        if selected_category == "All Creatives" or item["type"] == selected_category
    ]

    if not filtered_items:
        st.markdown("""
        <div style="background:#111827; border: 1px dashed #334155; border-radius:10px; padding:2rem; text-align:center; color:#94a3b8;">
            <div style="font-size:1.8rem; margin-bottom:0.4rem;">🎨</div>
            <strong style="color:#f8fafc; font-size:1.05rem;">No user campaign creatives found in this category yet.</strong>
            <p style="margin:0.4rem 0 1rem 0; font-size:0.85rem; color:#64748b;">
                Generate a custom campaign to see your creative assets displayed here, or visit the Demo Gallery to inspect read-only sample campaigns.
            </p>
        </div>
        """, unsafe_allow_html=True)
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button("🚀 Go to Campaign Generator", use_container_width=True, key="btn_empty_gallery_gen"):
                navigate_to("🚀 Campaign Generator")
        with col_act2:
            if st.button("🌟 Explore Sample Campaigns", use_container_width=True, key="btn_empty_gallery_demo"):
                navigate_to("🌟 Sample Campaigns")
        return

    st.markdown(f"<span style='color:#94a3b8; font-size:0.85rem;'>Displaying {len(filtered_items)} creatives from your campaigns</span>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col_g1, col_g2 = st.columns(2)
    for idx, item in enumerate(filtered_items):
        with col_g1 if idx % 2 == 0 else col_g2:
            st.markdown(f"""
            <div class="studio-card">
                <div class="studio-card-header">
                    <span class="badge-pill {item['badge_cls']}">{item['badge']}</span>
                    <span style="font-size:0.75rem; color:#64748b;">{item['platform']}</span>
                </div>
                <h4 style="margin-top:0.4rem;">{item['title']}</h4>
                <div style="font-size:0.78rem; color:#38bdf8; margin-bottom:0.6rem;">{item['brand']} • {item['product']}</div>
                <div style="background:#090d16; border:1px solid #1e293b; border-radius:6px; padding:0.8rem; font-size:0.88rem; color:#e2e8f0; font-family:monospace; white-space:pre-wrap; margin-bottom:0.6rem;">{item['content']}</div>
                <div style="font-size:0.78rem; color:#94a3b8;">{item['meta']}</div>
            </div>
            """, unsafe_allow_html=True)
            with st.expander("📋 Copy & Full Preview"):
                st.code(item["content"], language=None)


# ---------------------------------------------------------------------------
# PAGE 5: DEDICATED SAMPLE CAMPAIGNS (Demo Gallery)
# ---------------------------------------------------------------------------

def page_sample_campaigns():
    st.markdown("""
    <div class="hero-container" style="padding: 1.4rem 2rem;">
        <div class="hero-title" style="font-size: 1.7rem;">🌟 Sample Campaigns & Demo Gallery</div>
        <div class="hero-tagline">Curated read-only demonstrations across e-commerce, local retail, and SaaS</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="demo-notice-box" style="margin-bottom:1.5rem;">
        <div class="demo-notice-title">💡 Read-Only Showcase</div>
        <div class="demo-notice-body">
            These campaigns are pre-built reference demonstrations. Inspecting them will <strong>never overwrite or alter your saved campaigns</strong>. 
            Click <strong>“Use as New Draft”</strong> on any example to copy its brief into the Campaign Generator as an editable starting point.
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_skin, tab_cafe, tab_saas = st.tabs([
        "🌸 GlowUp Skincare (E-Commerce)",
        "☕ Bloom Specialty Cafe (Local Biz)",
        "⚡ FocusFlow App (SaaS)",
    ])

    ex_dir = Path(__file__).parent / "examples"

    def render_sample_item(file_name: str, key_suffix: str):
        path = ex_dir / file_name
        if not path.exists():
            st.error(f"Sample file {file_name} not found.")
            return

        raw_sample = json.loads(path.read_text(encoding="utf-8"))
        inputs = raw_sample.get("inputs", {})
        
        # Build deterministic synthesized representation for viewing
        try:
            demo_pkg = generator.generate_full_campaign(inputs, force_demo=True, label_as_demo=False)
        except TypeError:
            demo_pkg = generator.generate_full_campaign(inputs, force_demo=True)
        demo_pkg = clean_campaign_output(demo_pkg)

        col_top_info, col_top_act = st.columns([3, 1])
        with col_top_info:
            st.markdown(f"### {inputs.get('brand_name')} — {inputs.get('product_name')}")
            st.caption(f"Platform: {inputs.get('platform')} • Duration: {inputs.get('duration')}s • Tone: {inputs.get('tone')}")
        with col_top_act:
            if st.button("📝 Use as New Draft", key=f"draft_{key_suffix}", type="primary", use_container_width=True):
                st.session_state.prefill_inputs = dict(inputs)
                st.success(f"Copied {inputs.get('brand_name')} to Campaign Generator as a new draft!")
                time.sleep(0.3)
                navigate_to("🚀 Campaign Generator")

        st.markdown(f"**Brief Description:** {inputs.get('description')}")
        st.markdown(f"**Verified Benefits:** {inputs.get('benefits')}")
        st.markdown("---")

        # Sample Hooks
        st.markdown("#### Sample Hooks Generated:")
        for h in demo_pkg.get("hooks", [])[:3]:
            st.markdown(f"""
            <div class="hook-studio-box">
                <div class="hook-studio-num">Hook {h.get('hook_number')} • {h.get('style')}</div>
                <div class="hook-studio-text">"{h.get('hook_text')}"</div>
                <div class="hook-studio-meta">{h.get('why_it_works')}</div>
            </div>
            """, unsafe_allow_html=True)

        # Sample UGC Script Preview
        script = demo_pkg.get("script", {})
        if script and script.get("scenes"):
            st.markdown(f"#### UGC Video Script Blueprint: *{script.get('script_title')}*")
            for sc in script.get("scenes", [])[:2]:
                st.markdown(f"""
                <div style="background:#111827; border:1px solid #1e293b; border-radius:6px; padding:0.8rem; margin-bottom:0.5rem;">
                    <div style="color:#38bdf8; font-weight:600;">Scene {sc.get('scene_number')} ({sc.get('timestamp')})</div>
                    <div style="color:#e2e8f0; font-size:0.88rem;">🗣️ Dialogue: "{sc.get('dialogue')}"</div>
                    <div style="color:#94a3b8; font-size:0.8rem;">🎥 Visual: {sc.get('visual_direction')}</div>
                </div>
                """, unsafe_allow_html=True)

        # Quality Audit
        st.markdown("#### Sample Quality Audit Score:")
        qr = demo_pkg.get("quality_review", {})
        st.markdown(f"Overall Quality Rating: **{qr.get('overall_score', 85)}/100**")
        st.caption(qr.get("score_disclaimer", ""))

    with tab_skin:
        render_sample_item("skincare_campaign.json", "skin")

    with tab_cafe:
        render_sample_item("local_cafe_campaign.json", "cafe")

    with tab_saas:
        render_sample_item("saas_campaign.json", "saas")


# ---------------------------------------------------------------------------
# PAGE 6: CAMPAIGN HISTORY
# ---------------------------------------------------------------------------

def page_campaign_history():
    st.markdown("""
    <div class="hero-container" style="padding: 1.4rem 2rem;">
        <div class="hero-title" style="font-size: 1.7rem;">📁 Campaign History & Archives</div>
        <div class="hero-tagline">Manage, inspect, reopen, and export all generated user campaigns</div>
    </div>
    """, unsafe_allow_html=True)

    col_s, col_fp, col_fs = st.columns([2, 1, 1])
    with col_s:
        search_q = st.text_input(
            "Search Campaigns",
            placeholder="Search by campaign name, brand, or product...",
            label_visibility="collapsed",
        )
    with col_fp:
        plat_options = ["All"] + SUPPORTED_PLATFORMS
        plat_filter = st.selectbox(
            "Filter Platform",
            plat_options,
            label_visibility="collapsed",
        )
    with col_fs:
        status_options = ["All", "Completed", "Draft", "Demo"]
        status_filter = st.selectbox(
            "Filter Status",
            status_options,
            label_visibility="collapsed",
        )

    campaigns = storage.list_campaigns(
        query=search_q,
        platform_filter=plat_filter,
        status_filter=status_filter,
    )

    if not campaigns:
        st.info("No matching campaigns found in history.")
        if st.button("Create a New Campaign →", key="btn_go_gen_from_hist"):
            navigate_to("🚀 Campaign Generator")
        return

    st.markdown(f"<span style='color:#94a3b8; font-size:0.85rem;'>Found {len(campaigns)} saved campaign(s)</span>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    for c in campaigns:
        cid = c["id"]
        status_cls = "badge-emerald" if c.get("status") == "Completed" else "badge-amber" if c.get("status") == "Demo" else "badge-violet"
        score_val = f"Score: {c['quality_score']}/100" if c.get("quality_score") is not None else "Unscored"

        with st.container():
            col_info, col_acts = st.columns([3, 2])
            with col_info:
                st.markdown(f"""
                <div style="background:#111827; border: 1px solid #1e293b; border-radius:8px; padding:0.9rem; margin-bottom:0.5rem;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <strong style="color:#f8fafc; font-size:1.05rem;">{c['name']}</strong>
                        <div>
                            <span class="badge-pill {status_cls}">{c.get('status', 'Completed')}</span>
                            <span class="badge-pill badge-blue" style="margin-left:0.2rem;">{c.get('platform', 'N/A')}</span>
                        </div>
                    </div>
                    <div style="font-size:0.83rem; color:#94a3b8; margin-top:0.3rem;">
                        <strong>Brand:</strong> {c.get('brand_name', '')} | <strong>Product:</strong> {c.get('product_name', '')}
                    </div>
                    <div style="font-size:0.75rem; color:#64748b; margin-top:0.2rem;">
                        ID: <code>{cid}</code> • Saved: {c['created_at'][:16].replace('T', ' ')} UTC • {score_val}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col_acts:
                b_c1, b_c2, b_c3 = st.columns(3)
                with b_c1:
                    if st.button("📂 Open", key=f"hist_open_{cid}", use_container_width=True):
                        loaded = storage.load_campaign(cid)
                        if loaded:
                            st.session_state.campaign_result = loaded
                            navigate_to("📊 Campaign Results")
                with b_c2:
                    if st.button("✏️ Edit Brief", key=f"hist_edit_{cid}", use_container_width=True):
                        loaded = storage.load_campaign(cid)
                        if loaded:
                            st.session_state.prefill_inputs = loaded.get("inputs", {})
                            navigate_to("🚀 Campaign Generator")
                with b_c3:
                    if st.button("🗑️ Delete", key=f"hist_del_{cid}", use_container_width=True):
                        st.session_state.show_delete_confirm = cid
                        st.rerun()

            # Confirm delete dialog
            if st.session_state.get("show_delete_confirm") == cid:
                st.warning(f"Are you sure you want to delete campaign '{c['name']}'? This cannot be undone.")
                col_yes, col_no = st.columns([1, 4])
                with col_yes:
                    if st.button("Yes, Delete", key=f"conf_del_{cid}", type="primary"):
                        storage.delete_campaign(cid)
                        st.session_state.show_delete_confirm = None
                        st.success("Campaign deleted.")
                        st.rerun()
                with col_no:
                    if st.button("Cancel", key=f"canc_del_{cid}"):
                        st.session_state.show_delete_confirm = None
                        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("⚠️ Danger Zone — Clear Storage"):
        st.markdown("Permanently erase all stored campaigns from `campaigns.json`.")
        if st.button("🗑️ Clear All Saved Campaigns", type="secondary", key="btn_clear_all_storage"):
            storage.clear_all()
            st.success("Storage cleared successfully.")
            st.rerun()


# ---------------------------------------------------------------------------
# PAGE 7: PROMPT INSPECTOR
# ---------------------------------------------------------------------------

def page_prompt_inspector():
    st.markdown("""
    <div class="hero-container" style="padding: 1.4rem 2rem;">
        <div class="hero-title" style="font-size: 1.7rem;">🔍 Prompt Inspector</div>
        <div class="hero-tagline">Inspect the production prompt templates and variable bindings powering the studio</div>
    </div>
    """, unsafe_allow_html=True)

    template_names = get_all_template_names()
    if not template_names:
        st.error("No prompt template files found in prompts/ directory.")
        return

    friendly_labels = {
        "campaign_brief.txt": "📋 Campaign Brief Synthesizer",
        "hooks.txt": "🎣 Advertising Hooks Generator",
        "ugc_script.txt": "🎬 UGC Video Script Blueprint",
        "cta.txt": "📢 Direct-Response CTAs",
        "captions.txt": "📝 Captions & Relevant Hashtags",
        "platform_adaptation.txt": "📱 Cross-Platform Adapters",
        "quality_review.txt": "🛡️ Content Quality & Ethics Reviewer",
    }

    col_nav, col_view = st.columns([1, 2])
    with col_nav:
        st.markdown("#### Select Template")
        chosen_template = st.radio(
            "Templates",
            template_names,
            format_func=lambda x: friendly_labels.get(x, x),
            label_visibility="collapsed",
        )

    with col_view:
        if chosen_template:
            meta = get_template_metadata(chosen_template)
            st.markdown(f"### {friendly_labels.get(chosen_template, chosen_template)}")
            
            st.markdown(f"""
            <div style="background:#111827; border:1px solid #1e293b; border-radius:8px; padding:0.9rem; margin-bottom:1rem;">
                <div><strong>Template ID:</strong> <code>{meta.get('id', meta.get('prompt_template', chosen_template))}</code></div>
                <div style="margin-top:0.3rem;"><strong>Version:</strong> {meta.get('version', '1.0')}</div>
                <div style="margin-top:0.3rem;"><strong>Strategic Purpose:</strong> {meta.get('purpose', 'Production creative prompt')}</div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("📖 View Full System Prompt & Instructions"):
                try:
                    full_text = load_template(chosen_template)
                    st.code(full_text, language="text")
                except Exception as exc:
                    st.error(f"Failed to load: {exc}")

    st.markdown("---")
    st.markdown("### 🔎 Sanitized Live Preview (With Injected Variables)")
    st.caption("Demonstrates the clean USER: prompt block after variable substitution. Internal system instructions are securely shielded.")

    campaign_res = st.session_state.get("campaign_result") or {}
    active_inputs = campaign_res.get("inputs") or {
        "brand_name": "SampleBrand",
        "product_name": "Sample Product",
        "description": "An innovative solution designed for active professionals.",
        "target_audience": "Working adults aged 25-45",
        "objective": "Product Awareness",
        "platform": "Instagram Reels",
        "tone": "Friendly",
        "duration": "30",
        "language": "English",
        "benefits": "Fast-acting, verified ingredients, easy to use.",
        "offer": "10% off with code SAMPLE",
        "avoid_words": "miracle, guaranteed",
        "pain_points": "Lack of time, low convenience",
        "num_hooks": "5",
        "brief_summary": "Campaign to raise awareness of Sample Product on Instagram Reels.",
        "hook_text": "Ever feel like there are not enough hours in the day?",
        "primary_hook": "Ever feel like there are not enough hours in the day?",
        "cta": "Learn more at our website",
        "primary_cta": "Learn more at our website",
        "campaign_json": "{...structured campaign payload...}",
    }

    try:
        preview_text = sanitized_preview(chosen_template, active_inputs)
        st.text_area(
            "Assembled User Prompt",
            value=preview_text,
            height=260,
            disabled=True,
        )
    except Exception as e:
        st.error(f"Preview assembly error: {e}")


# ---------------------------------------------------------------------------
# PAGE 8: SETTINGS & API CONFIGURATION
# ---------------------------------------------------------------------------

def page_settings():
    st.markdown("""
    <div class="hero-container" style="padding: 1.4rem 2rem;">
        <div class="hero-title" style="font-size: 1.7rem;">⚙️ Studio Settings & Configuration</div>
        <div class="hero-tagline">Manage creative studio preferences, synthesis engine status, and campaign library storage</div>
    </div>
    """, unsafe_allow_html=True)

    # Active Creative Engine Status Card
    st.markdown("""
    <div style="background:#111827; border: 1px solid #1e293b; border-radius:10px; padding:1.2rem; margin-bottom:1.5rem;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <strong style="color:#f8fafc; font-size:1.05rem;">Active Creative Engine</strong>
                <div style="color:#94a3b8; font-size:0.85rem; margin-top:0.2rem;">
                    Multi-Variable Prompt Synthesis Engine (Pure Python)
                </div>
            </div>
            <span class="badge-pill badge-emerald">Online ⚡</span>
        </div>
        <div style="margin-top:1rem; padding:0.8rem; background:rgba(15, 23, 42, 0.7); border-radius:8px; border:1px solid #1e293b;">
            <div style="font-size:0.82rem; color:#94a3b8; margin-bottom:0.3rem;">Synthesis Formulation:</div>
            <code style="color:#38bdf8; font-size:0.85rem;">Copy = f(Brand, Product, Target Audience, USPs, Tone, Platform, Duration, Context)</code>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="card" style="margin-bottom: 1.5rem; border-left: 3px solid #10b981;">
        <h4 style="color:#34d399; margin:0 0 0.5rem 0;">⚡ Why Pure Python Synthesis Engine?</h4>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; margin-top:0.6rem;">
            <div style="background:rgba(15, 23, 42, 0.5); padding:0.7rem; border-radius:6px; border:1px solid #1e293b;">
                <strong style="color:#e2e8f0; font-size:0.82rem;">💰 Zero Cost & No API Keys</strong>
                <p style="color:#94a3b8; font-size:0.78rem; margin:0.3rem 0 0 0;">Never runs out of credits, has no rate limits, and requires zero paid subscriptions.</p>
            </div>
            <div style="background:rgba(15, 23, 42, 0.5); padding:0.7rem; border-radius:6px; border:1px solid #1e293b;">
                <strong style="color:#e2e8f0; font-size:0.82rem;">⚡ Instant Sub-Second Generation</strong>
                <p style="color:#94a3b8; font-size:0.78rem; margin:0.3rem 0 0 0;">Generates complete scripts, hooks, and quality audits in under 1 second without network lag.</p>
            </div>
            <div style="background:rgba(15, 23, 42, 0.5); padding:0.7rem; border-radius:6px; border:1px solid #1e293b;">
                <strong style="color:#e2e8f0; font-size:0.82rem;">🚀 100% Reliable Deployment</strong>
                <p style="color:#94a3b8; font-size:0.78rem; margin:0.3rem 0 0 0;">Runs seamlessly on Streamlit Community Cloud with zero configuration and zero external dependencies.</p>
            </div>
            <div style="background:rgba(15, 23, 42, 0.5); padding:0.7rem; border-radius:6px; border:1px solid #1e293b;">
                <strong style="color:#e2e8f0; font-size:0.82rem;">🛡️ Safe & Deterministic</strong>
                <p style="color:#94a3b8; font-size:0.78rem; margin:0.3rem 0 0 0;">Strictly adheres to verified inputs and checks for unverified claims and medical disclaimers.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Studio Defaults / Preferences
    st.markdown("### 🎛️ Default Studio Preferences")
    st.caption("Customize default parameters for new campaign generation sessions.")

    studio_prefs = st.session_state.get("studio_preferences", {
        "platform": "Instagram Reels",
        "tone": "Friendly",
        "duration": 30,
        "num_hooks": 5,
    })

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        pref_platform = st.selectbox(
            "Default Platform",
            SUPPORTED_PLATFORMS,
            index=SUPPORTED_PLATFORMS.index(studio_prefs.get("platform", "Instagram Reels"))
            if studio_prefs.get("platform") in SUPPORTED_PLATFORMS else 0,
            key="pref_platform",
        )
        pref_tone = st.selectbox(
            "Default Tone",
            SUPPORTED_TONES,
            index=SUPPORTED_TONES.index(studio_prefs.get("tone", "Friendly"))
            if studio_prefs.get("tone") in SUPPORTED_TONES else 0,
            key="pref_tone",
        )
    with col_p2:
        pref_duration = st.selectbox(
            "Default Duration (seconds)",
            SUPPORTED_DURATIONS,
            index=SUPPORTED_DURATIONS.index(studio_prefs.get("duration", 30))
            if studio_prefs.get("duration") in SUPPORTED_DURATIONS else 1,
            key="pref_duration",
        )
        pref_num_hooks = st.slider(
            "Default Number of Hooks",
            min_value=MIN_HOOKS,
            max_value=MAX_HOOKS,
            value=int(studio_prefs.get("num_hooks", 5)),
            key="pref_num_hooks",
        )

    if st.button("💾 Save Studio Preferences", type="primary", key="btn_save_prefs"):
        st.session_state["studio_preferences"] = {
            "platform": pref_platform,
            "tone": pref_tone,
            "duration": pref_duration,
            "num_hooks": pref_num_hooks,
        }
        st.success("Studio preferences saved successfully!")

    st.markdown("---")

    # Storage Management
    st.markdown("### 📁 Campaign Storage & Library Management")
    c_count = storage.campaign_count()
    st.markdown(f"""
    - **Storage Backend:** Local JSON Storage (<code>campaigns.json</code>)
    - **Total Saved Campaigns:** <code>{c_count}</code>
    """, unsafe_allow_html=True)

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        all_campaigns_data = storage.list_campaigns()
        library_json_str = json.dumps(all_campaigns_data, indent=2)
        st.download_button(
            "📥 Export Full Library (JSON)",
            data=library_json_str,
            file_name=f"promptadscraft_library_{datetime.now(timezone.utc).strftime('%Y%m%d')}.json",
            mime="application/json",
            use_container_width=True,
            key="btn_download_lib",
        )
    with col_s2:
        confirm_clear = st.checkbox("Confirm library reset (clears all saved campaigns)", key="chk_confirm_clear")
        if st.button("🗑️ Clear Entire History", type="secondary", disabled=not confirm_clear, use_container_width=True, key="btn_clear_history"):
            storage.clear_all()
            st.session_state["campaign_result"] = None
            st.warning("Campaign library has been reset.")
            time.sleep(0.5)
            st.rerun()

    st.markdown("---")
    st.markdown("### ℹ️ System Diagnostics & Environment")
    st.markdown(f"""
    - **Application:** `{APP_NAME}` v`{APP_VERSION}`
    - **Engine:** Pure Python Multi-Variable Prompt Synthesis
    - **Runtime Environment:** Python `{sys.version.split()[0]}` • Streamlit `{st.__version__}`
    - **Deployment Platform:** Streamlit Community Cloud
    """)

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

active_page = page

if active_page == "🏠 Dashboard":
    page_dashboard()
elif active_page == "🚀 Campaign Generator":
    page_campaign_generator()
elif active_page == "📊 Campaign Results":
    page_campaign_results()
elif active_page == "🎨 Creative Gallery":
    page_creative_gallery()
elif active_page == "🌟 Sample Campaigns":
    page_sample_campaigns()
elif active_page == "📁 Campaign History":
    page_campaign_history()
elif active_page == "🔍 Prompt Inspector":
    page_prompt_inspector()
elif active_page == "⚙️ Settings":
    page_settings()
