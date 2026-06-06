"""
Resume Builder Pro  –  Canva-style two-panel live editor.

Architecture
────────────
• LEFT  : scrollable form (6 tabs, live text inputs — no form wrapping)
• RIGHT : sticky PDF preview (auto-compiles on any content change)
• UNDO/REDO : 30-step history stack in session_state
• SETTINGS  : contextual explanations shown inline
"""

import streamlit as st
import json, os, base64, re, time, copy

from resume_builder.generators import build_pdf
from resume_builder.templates import TEMPLATES, register_templates
from resume_builder.utils.health_scorer import calculate_health_score
from resume_builder.parser.reader import (
    extract_pdf_layout_and_text,
    extract_docx_layout_and_text,
    extract_txt_text,
)
from resume_builder.parser.engine import (
    analyze_style_from_runs,
    segment_into_blocks,
    parse_mapped_blocks_to_json,
    calculate_fidelity_score,
)
from resume_builder.generators.custom_html import (
    compile_custom_html,
    analyze_html_template_styles,
)

# ═══════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════
st.set_page_config(
    page_title="Resume Builder Pro",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ═══════════════════════════════════════════════════════
# GLOBAL CSS  — Canva-style two-panel feel
# ═══════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Base — force light theme on Streamlit Cloud & local ── */
html, body, [data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section,
[data-testid="stVerticalBlock"],
.main .block-container {
  font-family: 'Inter', sans-serif !important;
  background: #F0F2F8 !important;
  color: #1E293B !important;
}

/* Force all generic text dark so cloud dark-mode doesn't override */
p, span, div, li, td, th, label,
h1, h2, h3, h4, h5, h6 {
  color: #1E293B;
}

/* Streamlit markdown elements */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {
  color: #1E293B !important;
}

#MainMenu, footer, [data-testid="stHeader"],
[data-testid="stDecoration"], [data-testid="stToolbar"] { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }

/* ── Modern App Padding ── */
.block-container {
  padding: 1.5rem 3rem !important;
  max-width: 1600px !important;
}
[data-testid="stAppViewContainer"] > .main { padding: 0 !important; }

/* ── Light Premium Top Bar Toolbar ── */
div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] {
  background: #FFFFFF !important;
  padding: 14px 20px !important;
  border-radius: 16px !important;
  border: 1px solid #E2E8F0 !important;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03) !important;
  margin-bottom: 24px !important;
  align-items: center !important;
}

/* Style selectboxes inside the top bar */
div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] .stSelectbox div[data-baseweb="select"] > div {
  border-radius: 10px !important;
  border: 1px solid #E2E8F0 !important;
  background-color: #F8FAFC !important;
  height: 38px !important;
  color: #1E293B !important;
}
div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] .stSelectbox div[data-baseweb="select"] span {
  color: #1E293B !important;
  font-weight: 500 !important;
  font-size: 0.82rem !important;
}
div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] .stSelectbox div[data-baseweb="select"] svg {
  fill: #1E293B !important;
}

/* Style buttons inside the top bar */
div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] button {
  background-color: #F8FAFC !important;
  border: 1px solid #E2E8F0 !important;
  color: #1E293B !important;
  border-radius: 10px !important;
  height: 38px !important;
  font-size: 0.83rem !important;
  font-weight: 600 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  box-shadow: none !important;
}
div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] button:hover:not(:disabled) {
  background-color: #F1F5F9 !important;
  border-color: #CBD5E1 !important;
  color: #1E293B !important;
}
div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] button:disabled {
  opacity: 0.5 !important;
  color: #94A3B8 !important;
}

/* Custom styling for color picker block inside top bar */
div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] div[data-testid="stColorPickerColorBlock"] {
  border-radius: 8px !important;
  border: 1px solid #E2E8F0 !important;
}
div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] .stColorPicker > div {
  margin-top: -6px !important;
}

/* ── Sticky preview card ── */
.preview-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0,0,0,.12);
  overflow: hidden;
  min-height: 600px;
}

/* ── Section headers inside form ── */
.sec-title {
  font-size: .78rem; font-weight: 700; color: #6366F1;
  text-transform: uppercase; letter-spacing: .08em;
  margin: 16px 0 8px; padding-bottom: 5px;
  border-bottom: 2px solid #EEF2FF;
}

/* ── Setting row with explanation ── */
.setting-row { margin-bottom: 12px; }
.setting-effect {
  display: inline-block; margin-top: 2px;
  font-size: .72rem; padding: 2px 8px;
  border-radius: 100px; font-weight: 600;
}
.eff-balanced { background: #DCFCE7; color: #15803D; }
.eff-compact  { background: #FEF9C3; color: #854D0E; }
.eff-spacious { background: #DBEAFE; color: #1D4ED8; }
.eff-tight    { background: #FEE2E2; color: #B91C1C; }
.eff-standard { background: #F1F5F9; color: #475569; }

/* ── Undo/Redo pill buttons ── */
.ur-btn {
  display: inline-flex; align-items: center; justify-content: center;
  width: 32px; height: 32px; border-radius: 8px;
  background: rgba(255,255,255,.12); color: #fff; font-size: .9rem;
  cursor: pointer; border: 1px solid rgba(255,255,255,.2);
  transition: background .15s;
}
.ur-btn:hover { background: rgba(255,255,255,.22); }
.ur-btn.disabled { opacity: .35; cursor: not-allowed; }

/* ── Streamlit widget overrides ── */
.stButton button {
  border-radius: 8px !important;
  font-family: 'Inter', sans-serif !important;
  font-weight: 600 !important; font-size: .83rem !important;
  transition: all .12s !important;
}
.stButton button[kind="primary"] {
  background: linear-gradient(135deg,#6366F1,#8B5CF6) !important;
  border: none !important; box-shadow: 0 2px 8px rgba(99,102,241,.3) !important;
  color: #fff !important;
}
.stButton button[kind="primary"]:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 14px rgba(99,102,241,.4) !important;
}

/* Ensure secondary buttons and other text blocks are readable */
.stButton button[kind="secondary"] {
  color: #1E293B !important;
  background-color: #F1F5F9 !important;
  border: 1px solid #CBD5E1 !important;
}
.stButton button[kind="secondary"]:hover {
  background-color: #E2E8F0 !important;
  border-color: #94A3B8 !important;
}

.stTextInput input, .stTextArea textarea {
  border-radius: 7px !important; border-color: #E2E8F0 !important;
  font-family: 'Inter', sans-serif !important; font-size: .82rem !important;
  padding: 6px 10px !important;
  background: #FAFBFF !important;
  color: #0F172A !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: #6366F1 !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,.12) !important;
  background: #fff !important;
  color: #0F172A !important;
}

/* Inputs Placeholders Contrast */
.stTextInput input::placeholder, .stTextArea textarea::placeholder {
  color: #64748B !important; opacity: 1 !important;
}
.stTextInput input::-webkit-input-placeholder, .stTextArea textarea::-webkit-input-placeholder {
  color: #64748B !important; opacity: 1 !important;
}
.stTextInput input::-moz-placeholder, .stTextArea textarea::-moz-placeholder {
  color: #64748B !important; opacity: 1 !important;
}
.stTextInput input:-ms-input-placeholder, .stTextArea textarea:-ms-input-placeholder {
  color: #64748B !important; opacity: 1 !important;
}

div[data-testid="stWidgetLabel"] p {
  font-size: .78rem !important; font-weight: 600 !important;
  color: #1E293B !important; margin-bottom: 2px !important;
}
div[data-testid="element-container"] { margin-bottom: 0.3rem !important; }

.stExpander {
  border: 1.5px solid #E2E8F0 !important; border-radius: 10px !important;
  background: #FAFBFF !important; margin-bottom: 5px !important;
  color: #1E293B !important;
}
.stExpander summary {
  font-size: .82rem !important; font-weight: 600 !important;
  color: #1E293B !important;
}
.stExpander summary:hover {
  color: #6366F1 !important;
}
.stExpander summary svg {
  fill: #1E293B !important;
}
.stExpander [data-testid="stExpanderDetails"] p,
.stExpander [data-testid="stExpanderDetails"] span,
.stExpander [data-testid="stExpanderDetails"] div,
.stExpander [data-testid="stExpanderDetails"] li {
  color: #1E293B !important;
}

.stTabs [data-baseweb="tab-list"] {
  background: #E2E8F0; border-radius: 10px; padding: 3px; gap: 2px;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 7px !important; font-family: 'Inter', sans-serif !important;
  font-size: .78rem !important; font-weight: 500 !important; padding: 5px 11px !important;
  color: #475569 !important;
}
.stTabs [aria-selected="true"] {
  background: #fff !important; box-shadow: 0 1px 4px rgba(0,0,0,.08) !important;
  color: #6366F1 !important; font-weight: 700 !important;
}
/* Slider */
.stSlider { padding: 0 2px !important; }
div[data-testid="stSlider"] { margin-bottom: 0 !important; }
div[data-testid="stSlider"] span {
  color: #1E293B !important;
}

/* ── Metric pill ── */
.kpi {
  background: #fff; border: 1.5px solid #E2E8F0; border-radius: 10px;
  padding: 10px 12px; text-align: center;
}
.kpi-lbl { font-size: .62rem; font-weight: 700; color: #94A3B8;
  text-transform: uppercase; letter-spacing: .07em; margin-bottom: 1px; }
.kpi-val { font-size: 1.7rem; font-weight: 800; line-height: 1.1; color: #1E293B !important; }
.c-green { color: #10B981 !important; } .c-amber { color: #F59E0B !important; } .c-red { color: #EF4444 !important; }

/* ── Import upload zone ── */
.upload-zone {
  border: 2px dashed #C7D2FE; border-radius: 12px;
  padding: 24px 16px; text-align: center; background: #EEF2FF;
  margin: 8px 0;
}

/* ── Divider ── */
.hdiv { border-top: 1.5px solid #E2E8F0; margin: 12px 0; }

/* Scrollbar styling */
.left-panel::-webkit-scrollbar { width: 5px; }
.left-panel::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 10px; }

/* General text visibility overrides inside main content area */
[data-testid="stAppViewContainer"] .main [data-testid="stMarkdownContainer"] p,
[data-testid="stAppViewContainer"] .main [data-testid="stMarkdownContainer"] span,
[data-testid="stAppViewContainer"] .main [data-testid="stMarkdownContainer"] li,
[data-testid="stAppViewContainer"] .main [data-testid="stMarkdownContainer"] h1,
[data-testid="stAppViewContainer"] .main [data-testid="stMarkdownContainer"] h2,
[data-testid="stAppViewContainer"] .main [data-testid="stMarkdownContainer"] h3,
[data-testid="stAppViewContainer"] .main [data-testid="stMarkdownContainer"] h4,
[data-testid="stAppViewContainer"] .main [data-testid="stMarkdownContainer"] h5,
[data-testid="stAppViewContainer"] .main [data-testid="stMarkdownContainer"] h6 {
  color: #1E293B !important;
}

/* Standard Streamlit metrics labels and values */
div[data-testid="stMetricLabel"] {
  color: #475569 !important;
}
div[data-testid="stMetricValue"] {
  color: #1E293B !important;
}

/* Standard selectbox contrast */
.main div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
  background-color: #FAFBFF !important;
  border: 1px solid #E2E8F0 !important;
  color: #1E293B !important;
}
.main div[data-testid="stSelectbox"] div[data-baseweb="select"] span {
  color: #1E293B !important;
}
.main div[data-testid="stSelectbox"] div[data-baseweb="select"] svg {
  fill: #1E293B !important;
}

/* Radio button text visibility */
div[data-testid="stRadio"] label span {
  color: #1E293B !important;
}

/* Checkbox labels */
div[data-testid="stCheckbox"] label span {
  color: #1E293B !important;
}

/* File uploader contrast */
div[data-testid="stFileUploader"] section {
  background-color: #FAFAFB !important;
  border: 1px dashed #C7D2FE !important;
}
div[data-testid="stFileUploader"] section * {
  color: #1E293B !important;
}

/* ── Onboarding Banner ─────────────────────────────────── */
.onboarding-banner {
  background: linear-gradient(135deg, #EEF2FF 0%, #F5F3FF 100%);
  border: 1.5px solid #C7D2FE;
  border-left: 4px solid #6366F1;
  border-radius: 12px;
  padding: 12px 18px;
  font-size: .86rem;
  color: #3730A3;
  line-height: 1.5;
  margin-bottom: 4px;
}
.onboarding-banner b { color: #312E81; }
.onboarding-banner .ob-step {
  display: inline-flex;
  align-items: center;
  background: rgba(99,102,241,.12);
  border-radius: 100px;
  padding: 2px 10px;
  margin: 0 3px;
  font-weight: 600;
  font-size: .82rem;
}

/* ── Tab Hint Chips ────────────────────────────────────── */
.tab-hint {
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-left: 3px solid #6366F1;
  border-radius: 8px;
  padding: 8px 13px;
  font-size: .8rem;
  color: #475569;
  margin-bottom: 14px;
  line-height: 1.45;
}
.tab-hint .th-icon { margin-right: 5px; }
.tab-hint b { color: #1E293B; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════
# Absolute project root — works regardless of working directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESUME_JSON  = os.path.join(PROJECT_ROOT, "resume.json")
DEFAULTS_FILE = os.path.join(PROJECT_ROOT, "resume_builder", "config", "defaults.json")

FITTING_OPTS = ["Auto Compress", "Keep Original", "Multi-Page"]
BUILTIN      = {"sejal_original","ats","modern","creative","minimal","two_column"}
ACCENT_PRESETS = {
    "Indigo": "#6366F1", "Blue": "#2563EB", "Emerald": "#10B981",
    "Rose": "#E11D48", "Violet": "#7C3AED", "Slate": "#475569",
}

# Load settings defaults from config file if available
app_defaults = {
    "template": "sejal_original",
    "color": "#6366F1",
    "margins": 20,
    "fscale": 1.0,
    "fitting": FITTING_OPTS[0],
    "compact": False,
    "locked": False
}
if os.path.exists(DEFAULTS_FILE):
    try:
        with open(DEFAULTS_FILE, "r", encoding="utf-8") as f:
            loaded_defaults = json.load(f)
            app_defaults.update(loaded_defaults)
    except Exception:
        pass

DEFAULT = {
    "personal": {
        "name": "SEJAL BHAGAT", "location": "Nagpur, India",
        "phone": "+91 9022644273", "email": "bhagatsejal08@gmail.com",
        "linkedin": {"display": "linkedin/Sejal-Bhagat", "url": "https://linkedin.com/in/Sejal-Bhagat"},
        "github":   {"display": "github.com/SejalBhagat03", "url": "https://github.com/SejalBhagat03"},
    },
    "summary": "Final-year Computer Science student with full-stack development experience.",
    "experience": [], "projects": [],
    "technical_skills": {
        "Programming": "C++, Python, JavaScript",
        "Frontend": "HTML, CSS, React.js",
        "Tools": "Git, VS Code, Postman",
    },
    "achievements": [], "education": [], "position_of_responsibility": [],
}

DEMO_RESUME = {
    "personal": {
        "name": "Sejal Bhagat", "location": "Nagpur, India",
        "phone": "+91 9022644273", "email": "bhagatsejal08@gmail.com",
        "linkedin": {"display": "linkedin/Sejal-Bhagat", "url": "https://linkedin.com/in/Sejal-Bhagat"},
        "github":   {"display": "github.com/SejalBhagat03", "url": "https://github.com/SejalBhagat03"},
    },
    "summary": "Final-year Computer Science student with full-stack development experience working on React and Python.",
    "experience": [
        {
            "role": "Software Engineering Intern",
            "company": "TechCorp Solutions",
            "location": "Remote",
            "period": "June 2023 - Aug 2023",
            "technologies": "React, Python, Django",
            "bullets": [
                "Built a web application for labor logs.",
                "Integrated RESTful API endpoints for secure database CRUD actions.",
                "Optimized rendering speed of application views."
            ]
        }
    ],
    "projects": [
        {
            "title": "Labour Management App",
            "link": "https://github.com/SejalBhagat03/labour-management-app",
            "date": "2023",
            "tools": "React, Node.js, MongoDB",
            "bullets": [
                "Developed a role-based dashboard for materials tracking.",
                "Designed NoSQL collection schemas for labor statistics."
            ]
        }
    ],
    "technical_skills": {
        "Programming": "C++, Python, JavaScript, TypeScript",
        "Frontend": "HTML, CSS, React, Redux",
        "Backend": "Node.js, MongoDB, SQL"
    },
    "achievements": [
        "Won 1st place in regional tech hackathon 2023."
    ],
    "education": [
        {
            "degree": "B.E. Computer Science & Engineering",
            "institution": "Nagpur Institute of Technology",
            "details": "CGPA: 9.1/10",
            "period": "2020 - 2024"
        }
    ],
    "position_of_responsibility": []
}


# ═══════════════════════════════════════════════════════
# SESSION STATE BOOTSTRAP
# ═══════════════════════════════════════════════════════
def _s(k, v):
    if k not in st.session_state:
        st.session_state[k] = v

_s("resume",      DEFAULT.copy())
_s("template",    app_defaults["template"])
_s("color",       app_defaults["color"])
_s("margins",     app_defaults["margins"])
_s("fscale",      app_defaults["fscale"])
_s("fitting",     app_defaults["fitting"])
_s("compact",     app_defaults["compact"])
_s("locked",      app_defaults["locked"])
_s("last_hash",   "")
_s("pdf_b64",     None)
_s("pdf_raw",     None)
_s("cok",         False)
_s("cmsg",        "")
_s("compile_ts",  0.0)
# Undo/Redo stacks
_s("undo_stack",  [])
_s("redo_stack",  [])
_s("last_resume_hash", "")
_s("navigation_page", "workspace")
# Import wizard
_s("show_import", False)
_s("wiz_step",    "upload")
_s("wiz_blk",     [])
_s("wiz_lay",     None)
# Profile versions manager
_s("show_create_profile", False)
_s("create_profile_type", "new")
_s("show_delete_confirm", False)


# ═══════════════════════════════════════════════════════
# DATA I/O
# ═══════════════════════════════════════════════════════
@st.cache_data(ttl=60, show_spinner=False)
def _read_json(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return copy.deepcopy(DEFAULT)

def get_profile_path() -> str:
    if "current_profile_path" not in st.session_state:
        st.session_state.current_profile_path = os.path.join(PROJECT_ROOT, "resume.json")
    return st.session_state.current_profile_path

def save_to_disk(d: dict):
    with open(get_profile_path(), "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)
    _read_json.clear()

def load_from_disk() -> dict:
    return _read_json(get_profile_path())

def list_profile_options() -> dict:
    versions_dir = os.path.join(PROJECT_ROOT, "resume_versions")
    os.makedirs(versions_dir, exist_ok=True)
    options = {
        "Default Profile": os.path.join(PROJECT_ROOT, "resume.json")
    }
    # List all custom profiles in the resume_versions directory
    try:
        for fname in os.listdir(versions_dir):
            if fname.endswith(".json"):
                base = os.path.splitext(fname)[0]
                display_name = base.replace("_", " ").title() + " Profile"
                options[display_name] = os.path.join(versions_dir, fname)
    except Exception:
        pass
    return options


# ═══════════════════════════════════════════════════════
# UNDO / REDO
# ═══════════════════════════════════════════════════════
MAX_HISTORY = 30

def push_undo(old_state: dict):
    """Push old state onto undo stack before a change."""
    stack = st.session_state.undo_stack
    stack.append(copy.deepcopy(old_state))
    if len(stack) > MAX_HISTORY:
        stack.pop(0)
    st.session_state.undo_stack = stack
    st.session_state.redo_stack = []   # clear redo on new action

def do_undo():
    if not st.session_state.undo_stack:
        return
    st.session_state.redo_stack.append(copy.deepcopy(st.session_state.resume))
    st.session_state.resume = st.session_state.undo_stack.pop()
    st.session_state.last_hash = ""
    save_to_disk(st.session_state.resume)
    st.rerun()

def do_redo():
    if not st.session_state.redo_stack:
        return
    st.session_state.undo_stack.append(copy.deepcopy(st.session_state.resume))
    st.session_state.resume = st.session_state.redo_stack.pop()
    st.session_state.last_hash = ""
    save_to_disk(st.session_state.resume)
    st.rerun()


# ═══════════════════════════════════════════════════════
# RESUME HASH  (for change detection)
# ═══════════════════════════════════════════════════════
def resume_hash(d: dict, C: str, M: int, FS: float, tid: str, FT: str) -> str:
    raw = json.dumps(d, sort_keys=True) + f"|{C}|{M}|{FS}|{tid}|{FT}"
    return str(hash(raw))


# ═══════════════════════════════════════════════════════
# PDF COMPILE
# ═══════════════════════════════════════════════════════
def maybe_compile(d: dict, template_id: str, C: str, M: int, FS: float, FT: str):
    """Compile PDF only when content hash changed."""
    h = resume_hash(d, C, M, FS, template_id, FT)
    if h == st.session_state.last_hash and st.session_state.pdf_b64:
        return   # nothing changed
    st.session_state.last_hash = h
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    ctx = get_script_run_ctx()
    session_id = ctx.session_id if ctx else "default"
    pdf_out = os.path.join("resume_builder","exports","pdf",f"live_{session_id}.pdf")
    os.makedirs(os.path.dirname(pdf_out), exist_ok=True)
    ok, msg = build_pdf(
        data=d, template_id=template_id,
        pdf_filename=pdf_out,
        accent_color=C, font_scale=FS, margin_size=M,
        auto_compress=(FT == FITTING_OPTS[0]),
        allow_multi_page=(FT == FITTING_OPTS[2]),
        aggressive_compact=False, layout_locked=False,
    )
    st.session_state.cok  = ok
    st.session_state.cmsg = msg
    if ok:
        with open(pdf_out,"rb") as pf: raw = pf.read()
        st.session_state.pdf_raw = raw
        st.session_state.pdf_b64 = base64.b64encode(raw).decode()


# ═══════════════════════════════════════════════════════
# TEMPLATE HELPERS
# ═══════════════════════════════════════════════════════
def save_extracted_template(layout: dict, name: str) -> str:
    clean = re.sub(r"[^a-z0-9]","_", name.lower()).strip("_") or "custom"
    tdir  = os.path.join("resume_builder","templates",clean)
    os.makedirs(tdir, exist_ok=True)
    with open(os.path.join(tdir,"layout.json"),"w",encoding="utf-8") as f:
        json.dump(layout,f,indent=2)
    with open(os.path.join(tdir,"metadata.json"),"w",encoding="utf-8") as f:
        json.dump({"name":name.replace("_"," ").title(),
                   "description":"Extracted from uploaded resume.",
                   "ats_friendly":True},f,indent=2)
    with open(os.path.join(tdir,"template.py"),"w",encoding="utf-8") as f:
        f.write("from resume_builder.templates.extracted.template import ExtractedLayoutTemplate\n"
                f"class CustomTemplate_{clean}(ExtractedLayoutTemplate):\n    pass\n")
    register_templates()
    return clean


# ═══════════════════════════════════════════════════════
# HELPERS – explanatory labels
# ═══════════════════════════════════════════════════════
def margin_label(m: int) -> tuple:
    if m <= 12:   return ("Tight layout",   "eff-tight")
    if m <= 18:   return ("Compact layout", "eff-compact")
    if m <= 24:   return ("Balanced",       "eff-balanced")
    return             ("Spacious layout", "eff-spacious")

def fscale_label(fs: float) -> tuple:
    if fs <= 0.80: return ("More content per page", "eff-compact")
    if fs <= 0.95: return ("Slightly compact",       "eff-compact")
    if fs <= 1.05: return ("Standard readability",   "eff-standard")
    if fs <= 1.15: return ("Larger text",            "eff-balanced")
    return              ("Large text / fewer items", "eff-spacious")


# ═══════════════════════════════════════════════════════
# INPUT SANITIZATION
# ═══════════════════════════════════════════════════════
_SAFE_TAGS = {"b", "i", "em", "strong", "u", "br", "font", "a", "sup", "sub"}

def sanitize_html(text: str) -> str:
    """Strip dangerous HTML tags, keeping only safe formatting tags for ReportLab."""
    if not text:
        return text
    # Remove script/style/img/iframe/object/embed tags entirely (with content for script/style)
    text = re.sub(r'<\s*(script|style)[^>]*>.*?</\s*\1\s*>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Remove dangerous self-closing or void tags
    text = re.sub(r'<\s*/?\s*(?:img|iframe|object|embed|link|meta|form|input|button|select|textarea)\b[^>]*/?>', '', text, flags=re.IGNORECASE)
    # Allow only safe tags; strip everything else
    def _tag_filter(m):
        tag_name = re.match(r'<\s*/?\s*(\w+)', m.group(0))
        if tag_name and tag_name.group(1).lower() in _SAFE_TAGS:
            return m.group(0)
        return ''
    text = re.sub(r'<[^>]+>', _tag_filter, text)
    return text


# ═══════════════════════════════════════════════════════
# COLLECT RESUME FROM WIDGET KEYS  (live, no st.form)
# ═══════════════════════════════════════════════════════
def collect_resume() -> dict:
    """Build resume dict from live widget session-state keys."""
    ss = st.session_state
    d  = st.session_state.resume   # fallback for missing keys

    def g(key, fallback=""):
        return sanitize_html(ss.get(key, fallback))

    # personal
    personal = {
        "name":     g("f_nm",  d.get("personal",{}).get("name","")),
        "email":    g("f_em",  d.get("personal",{}).get("email","")),
        "phone":    g("f_ph",  d.get("personal",{}).get("phone","")),
        "location": g("f_lc",  d.get("personal",{}).get("location","")),
        "linkedin": {
            "display": g("f_lid", d.get("personal",{}).get("linkedin",{}).get("display","")),
            "url":     g("f_liu", d.get("personal",{}).get("linkedin",{}).get("url","")),
        },
        "github": {
            "display": g("f_ghd", d.get("personal",{}).get("github",{}).get("display","")),
            "url":     g("f_ghu", d.get("personal",{}).get("github",{}).get("url","")),
        },
    }

    # summary
    summary = g("f_summ", d.get("summary",""))

    # experience
    exp_data = []
    for i, exp in enumerate(d.get("experience",[])):
        ro = g(f"f_er{i}", exp.get("role",""))
        co = g(f"f_ec{i}", exp.get("company",""))
        ll = g(f"f_el{i}", exp.get("location",""))
        pe = g(f"f_ep{i}", exp.get("period",""))
        tc = g(f"f_et{i}", exp.get("technologies",""))
        bs = g(f"f_eb{i}", "\n".join(exp.get("bullets",[])))
        exp_data.append({"role":ro,"company":co,"location":ll,"period":pe,
                         "technologies":tc,
                         "bullets":[x.strip() for x in bs.split("\n") if x.strip()]})

    # projects
    proj_data = []
    for i, pr in enumerate(d.get("projects",[])):
        ti = g(f"f_pt{i}", pr.get("title",""))
        lk = g(f"f_plk{i}", pr.get("link",""))
        tl = g(f"f_ptl{i}", pr.get("tools",""))
        dt = g(f"f_pdt{i}", pr.get("date",""))
        bs = g(f"f_pb{i}", "\n".join(pr.get("bullets",[])))
        proj_data.append({"title":ti,"link":lk,"date":dt,"tools":tl,
                          "bullets":[x.strip() for x in bs.split("\n") if x.strip()]})

    # skills — only collect edits to existing rows; new category is added via the ➕ button
    sk = d.get("technical_skills",{})
    sk_data = {}
    for i, k in enumerate(sk.keys()):
        nk = g(f"f_sk{i}", k)
        nv = g(f"f_sv{i}", sk[k])
        if nk: sk_data[nk] = nv

    # achievements
    achl_raw = g("f_ach", "\n".join(d.get("achievements",[])))
    achievements = [a.strip() for a in achl_raw.split("\n") if a.strip()]

    # education
    edu_data = []
    for i, edu in enumerate(d.get("education",[])):
        dg  = g(f"f_ed{i}", edu.get("degree",""))
        det = g(f"f_edd{i}", edu.get("details",""))
        ins = g(f"f_ei{i}", edu.get("institution",""))
        pp  = g(f"f_epp{i}", edu.get("period",""))
        edu_data.append({"degree":dg,"institution":ins,"details":det,"period":pp})

    # positions
    por_data = []
    for i, por in enumerate(d.get("position_of_responsibility",[])):
        rr = g(f"f_prr{i}", por.get("role",""))
        pp = g(f"f_prp{i}", por.get("period",""))
        bs = g(f"f_prb{i}", "\n".join(por.get("bullets",[])))
        por_data.append({"role":rr,"period":pp,
                         "bullets":[x.strip() for x in bs.split("\n") if x.strip()]})

    return {
        "personal": personal,
        "summary": summary,
        "experience": exp_data,
        "projects": proj_data,
        "technical_skills": sk_data,
        "achievements": achievements,
        "education": edu_data,
        "position_of_responsibility": por_data,
    }


# ═══════════════════════════════════════════════════════
# REGISTER TEMPLATES
# ═══════════════════════════════════════════════════════
register_templates()
ALL_TEMPLATES = TEMPLATES

d  = st.session_state.resume
C  = st.session_state.color
M  = st.session_state.margins
FS = st.session_state.fscale
FT = st.session_state.fitting
TID = st.session_state.template

# Load resume.json on first run
if "resume_loaded" not in st.session_state:
    loaded = load_from_disk()
    if loaded != DEFAULT:
        st.session_state.resume = loaded
        d = st.session_state.resume
    st.session_state.resume_loaded = True


# ═══════════════════════════════════════════════════════
# ① TOP BAR
# ═══════════════════════════════════════════════════════
st.markdown('<div id="top-bar-marker"></div>', unsafe_allow_html=True)

# Determine columns layout dynamically based on current page view
page = st.session_state.navigation_page
if page == "workspace":
    bar_brand, bar_page, bar_tpl, bar_clr, bar_ur, bar_mode = st.columns([2.5, 2.5, 2.5, 2.2, 2.3, 2.5], gap="small")
else:
    bar_brand, bar_page, bar_empty, bar_mode = st.columns([2.5, 2.5, 7.0, 2.5], gap="small")

with bar_brand:
    st.markdown(
        '<div style="height: 38px; display: flex; align-items: center; padding-left: 4px;">'
        '<span style="font-weight:800;font-size:1.1rem;color:#1E293B;letter-spacing:-.02em;">'
        '📄 Resume <em style="font-style:normal;color:#6366F1;">Builder</em> Pro</span>'
        '</div>', unsafe_allow_html=True
    )

with bar_page:
    nav1, nav2 = st.columns(2)
    with nav1:
        if st.button(
            "📄 Editor",
            key="nav_to_editor",
            type="primary" if page == "workspace" else "secondary",
            use_container_width=True,
            help="Resume Editor — edit content and preview PDF",
        ):
            if page != "workspace":
                st.session_state.navigation_page = "workspace"
                st.rerun()
    with nav2:
        if st.button(
            "💼 Career",
            key="nav_to_career",
            type="primary" if page == "career" else "secondary",
            use_container_width=True,
            help="Career Center — analyze, optimize, GitHub import",
        ):
            if page != "career":
                st.session_state.navigation_page = "career"
                st.rerun()

if page == "workspace":
    with bar_tpl:
        tpl_names  = {k: v["name"] for k, v in ALL_TEMPLATES.items()}
        tpl_list   = list(tpl_names.keys())
        cur_idx    = tpl_list.index(TID) if TID in tpl_list else 0
        new_tpl = st.selectbox(
            "Template",
            options=tpl_list,
            format_func=lambda k: tpl_names[k],
            index=cur_idx,
            key="topbar_tpl",
            label_visibility="collapsed",
        )
        if new_tpl != TID:
            st.session_state.template = new_tpl
            st.session_state.last_hash = ""
            TID = new_tpl
            st.rerun()

    with bar_clr:
        accent_options = list(ACCENT_PRESETS.keys()) + ["Custom"]
        cur_accent = next((n for n, v in ACCENT_PRESETS.items() if v == C), "Custom")
        sel_accent = st.selectbox(
            "Accent",
            options=accent_options,
            index=accent_options.index(cur_accent),
            key="topbar_accent",
            label_visibility="collapsed",
        )
        if sel_accent == "Custom":
            new_color = st.color_picker("Custom", value=C, key="custom_color_picker", label_visibility="collapsed")
        else:
            new_color = ACCENT_PRESETS[sel_accent]
        if new_color != C:
            st.session_state.color = new_color
            st.session_state.last_hash = ""
            C = new_color
            st.rerun()

    with bar_ur:
        uc1, uc2, uc3 = st.columns([1, 1, 1.4])
        with uc1:
            can_undo = len(st.session_state.undo_stack) > 0
            if st.button("↩", key="btn_undo", disabled=not can_undo,
                         help="Undo last change", use_container_width=True):
                do_undo()
        with uc2:
            can_redo = len(st.session_state.redo_stack) > 0
            if st.button("↪", key="btn_redo", disabled=not can_redo,
                         help="Redo last change", use_container_width=True):
                do_redo()
        with uc3:
            st.markdown(
                f'<div style="font-size:.7rem;font-weight:600;color:#64748B;text-align:center;padding-top:10px;white-space:nowrap;">'
                f'{len(st.session_state.undo_stack)} steps</div>',
                unsafe_allow_html=True
            )

    with bar_mode:
        col_imp, col_demo = st.columns(2)
        with col_imp:
            if st.button("Import 📥", key="btn_import", use_container_width=True, type="secondary"):
                st.session_state.show_import = not st.session_state.show_import
                st.rerun()
        with col_demo:
            if st.button("Demo ⚡", key="btn_demo_workspace", use_container_width=True, type="primary"):
                st.session_state.resume = copy.deepcopy(DEMO_RESUME)
                st.session_state.github_username = "sejalbhagat03"
                st.session_state.target_role = "Frontend Developer"
                st.session_state.navigation_page = "career"
                st.session_state.last_hash = ""
                st.rerun()

else:
    # Career Center top bar
    with bar_mode:
        col_back, col_demo = st.columns(2)
        with col_back:
            if st.button("Editor 📄", key="btn_back_editor", use_container_width=True, type="secondary"):
                st.session_state.navigation_page = "workspace"
                st.rerun()
        with col_demo:
            if st.button("Demo ⚡", key="btn_demo_career", use_container_width=True, type="primary"):
                st.session_state.resume = copy.deepcopy(DEMO_RESUME)
                st.session_state.github_username = "sejalbhagat03"
                st.session_state.target_role = "Frontend Developer"
                st.session_state.last_hash = ""
                st.rerun()

# ── First-run onboarding banner (workspace only) ─────────────────────────
if page == "workspace" and not st.session_state.get("onboarding_dismissed"):
    ob_main, ob_close = st.columns([11, 1])
    with ob_main:
        st.markdown(
            '<div class="onboarding-banner">'
            '👋 <b>Welcome to Resume Builder Pro!</b>&nbsp; '
            'Fill in your details using the tabs on the <span class="ob-step">⬅ left panel</span>, '
            'and your resume updates live in the <span class="ob-step">preview ➡</span>. '
            'Switch to <b>💼 Career</b> in the top bar to access gap analysis, GitHub import, and more tools.'
            '</div>',
            unsafe_allow_html=True,
        )
    with ob_close:
        if st.button("✕", key="dismiss_onboarding", help="Dismiss this tip"):
            st.session_state.onboarding_dismissed = True
            st.rerun()

# Clean margin
st.markdown('<div style="margin-bottom: 8px;"></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# ② IMPORT WIZARD (collapsible panel below top bar)
# ═══════════════════════════════════════════════════════
if st.session_state.show_import:
    with st.container():
        st.markdown('<div style="background:#EEF2FF;border:1.5px solid #C7D2FE;'
                    'border-radius:12px;padding:16px 18px;margin:10px 0;">', unsafe_allow_html=True)
        st.markdown("#### 📥 Import Resume (PDF / DOCX / TXT)")

        if st.session_state.wiz_step == "upload":
            ic1, ic2 = st.columns([3,1])
            with ic1:
                uf = st.file_uploader("Drop your resume file here", type=["pdf","docx","txt"], key="imp_file")
            with ic2:
                do_ext = st.checkbox("Save as reusable template", value=True, key="imp_do_ext")
                tname  = st.text_input("Template name", "my_style", key="imp_tname")

            if uf and st.button("🚀 Extract & Import", type="primary", key="imp_go"):
                with st.spinner("Analysing…"):
                    tdir = os.path.join("resume_builder","data","temp")
                    os.makedirs(tdir, exist_ok=True)
                    tp = os.path.join(tdir, uf.name)
                    with open(tp,"wb") as tf: tf.write(uf.getbuffer())
                    ext = uf.name.rsplit(".",1)[-1].lower()
                    txt, lcfg = "", None
                    try:
                        if ext == "txt":
                            txt  = extract_txt_text(tp)
                            lcfg = {"margins":{"top":20,"bottom":20,"left":36,"right":36},
                                    "header":{"alignment":0,"name_font_size":18.,"contact_font_size":8.5},
                                    "sections":{"title_font_size":10.,"border_below":True,
                                                "border_above":False,"border_color":"#000000"},
                                    "body":{"font_size":8.,"leading":10.5,"bullet_indent":15}}
                        elif ext == "pdf":
                            txt, runs = extract_pdf_layout_and_text(tp)
                            lcfg = analyze_style_from_runs(runs)
                        elif ext == "docx":
                            txt, dd = extract_docx_layout_and_text(tp)
                            lcfg = analyze_style_from_runs(dd.get("runs",[]),dd.get("margins"))
                    except Exception as ex:
                        st.error(f"Extraction error: {ex}")
                    finally:
                        try: os.remove(tp)
                        except: pass
                    if txt:
                        st.session_state.wiz_blk  = segment_into_blocks(txt)
                        st.session_state.wiz_lay  = lcfg
                        st.session_state.wiz_step = "wizard"
                        st.session_state["_do_ext"] = do_ext
                        st.session_state["_tname"]  = tname
                        st.rerun()
                    else:
                        st.error("No text found — try another format.")

        elif st.session_state.wiz_step == "wizard":
            st.markdown("**Review extracted sections — adjust categories if needed:**")
            CATS = {"personal":"👤 Personal","summary":"📝 Summary",
                    "experience":"💼 Experience","projects":"🚀 Projects",
                    "skills":"🛠️ Skills","education":"🎓 Education",
                    "achievements":"🏆 Achievements",
                    "position_of_responsibility":"🤝 Positions","ignore":"❌ Ignore"}
            mapped = []
            for i, b in enumerate(st.session_state.wiz_blk):
                ic = b.get("inferred_category","ignore")
                di = list(CATS).index(ic) if ic in CATS else len(CATS)-1
                wa, wb = st.columns([.4,.6])
                with wa:
                    st.markdown(f"**`{b['header']}`**")
                    sc = st.selectbox("Category",list(CATS),format_func=lambda x:CATS[x],
                                      index=di,key=f"wz_{i}")
                with wb:
                    st.text_area("Preview","\\n".join(b["lines"][:3]),
                                 height=60,disabled=True,key=f"wz_pv{i}")
                mapped.append({"header":b["header"],"category":sc,"lines":b["lines"]})

            wz1, wz2 = st.columns(2)
            with wz1:
                if st.button("❌ Cancel", key="wz_cancel", use_container_width=True):
                    st.session_state.wiz_step = "upload"
                    st.session_state.wiz_blk  = []
                    st.session_state.wiz_lay  = None
                    st.rerun()
            with wz2:
                if st.button("✅ Confirm & Import", type="primary", key="wz_ok", use_container_width=True):
                    parsed = parse_mapped_blocks_to_json(mapped)
                    push_undo(st.session_state.resume)
                    st.session_state.resume = parsed
                    if st.session_state.get("_do_ext") and st.session_state.wiz_lay:
                        tn = st.session_state.get("_tname","my_style")
                        rn = save_extracted_template(st.session_state.wiz_lay, tn)
                        st.session_state.template = rn
                        TID = rn
                    save_to_disk(parsed)
                    st.session_state.last_hash = ""
                    st.session_state.wiz_step = "upload"
                    st.session_state.wiz_blk  = []
                    st.session_state.wiz_lay  = None
                    st.session_state.show_import = False
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# ③ TWO-PANEL LAYOUT OR CAREER CENTER
# ═══════════════════════════════════════════════════════
if st.session_state.navigation_page == "career":
    from resume_builder.career_dashboard import show_career_center
    show_career_center()
    st.stop()

left_col, right_col = st.columns([1.05, 1], gap="small")


# ─────────────────────────────────────────────────────
# LEFT PANEL — Form Editor
# ─────────────────────────────────────────────────────
with left_col:
    if "editor_notification" in st.session_state and st.session_state.editor_notification:
        st.success(st.session_state.editor_notification)
        st.session_state.editor_notification = None  # Clear notification

    d = st.session_state.resume

    # ── DOMAIN RESUME PROFILES ──
    st.markdown('<div class="sec-title" style="margin-top: 5px; margin-bottom: 5px;">Domain Resume Profiles</div>', unsafe_allow_html=True)
    profiles = list_profile_options()
    
    # Reverse lookup path to find the current active display name
    curr_path = get_profile_path()
    curr_display = "Default Profile"
    for name, path in profiles.items():
        if os.path.abspath(path) == os.path.abspath(curr_path):
            curr_display = name
            break
            
    # If the current path is not in the options (e.g. deleted or moved), fallback to Default
    if curr_display not in profiles:
        curr_display = "Default Profile"
        st.session_state.current_profile_path = os.path.join(PROJECT_ROOT, "resume.json")
        st.session_state.resume = load_from_disk()
        d = st.session_state.resume
        st.rerun()

    # Dropdown to switch profiles + Action buttons
    p_sel, p_actions = st.columns([3, 1.8])
    with p_sel:
        selected_name = st.selectbox(
            "Active Profile Selection",
            options=list(profiles.keys()),
            index=list(profiles.keys()).index(curr_display),
            key="profile_selector_dropdown",
            label_visibility="collapsed",
            help="Switch between different domain resumes (e.g., AI/ML, Full Stack). Each profile is saved independently."
        )
        if selected_name != curr_display:
            st.session_state.current_profile_path = profiles[selected_name]
            st.session_state.resume = load_from_disk()
            st.session_state.last_hash = ""
            st.rerun()
            
    with p_actions:
        col_new, col_dup, col_del = st.columns(3)
        with col_new:
            btn_new = st.button("➕", help="Create a new blank profile", use_container_width=True)
        with col_dup:
            btn_dup = st.button("👥", help="Duplicate current profile", use_container_width=True)
        with col_del:
            is_default = (selected_name == "Default Profile")
            btn_del = st.button("🗑️", help="Delete current profile", disabled=is_default, use_container_width=True)

    # Forms for profile creation / duplication / deletion
    if btn_new:
        st.session_state.show_create_profile = True
        st.session_state.create_profile_type = "new"
        st.session_state.show_delete_confirm = False
        st.rerun()
        
    if btn_dup:
        st.session_state.show_create_profile = True
        st.session_state.create_profile_type = "duplicate"
        st.session_state.show_delete_confirm = False
        st.rerun()
        
    if btn_del:
        st.session_state.show_delete_confirm = True
        st.session_state.show_create_profile = False
        st.rerun()

    # Show new/duplicate profile form
    if st.session_state.get("show_create_profile", False):
        p_type = st.session_state.create_profile_type
        action_verb = "Create New" if p_type == "new" else "Duplicate Current"
        with st.form("create_profile_form", clear_on_submit=True):
            st.markdown(f"**{action_verb} Profile**")
            new_name = st.text_input("Profile Name (e.g. AI ML Engineer, Backend Developer)", placeholder="AI ML Engineer")
            fc1, fc2 = st.columns(2)
            with fc1:
                submit = st.form_submit_button("Confirm", use_container_width=True, type="primary")
            with fc2:
                cancel = st.form_submit_button("Cancel", use_container_width=True)
                
            if submit and new_name.strip():
                clean_name = re.sub(r"[^a-zA-Z0-9\s_-]", "", new_name).strip()
                file_base = clean_name.lower().replace(" ", "_")
                if file_base:
                    new_file_name = f"{file_base}.json"
                    new_path = os.path.join(PROJECT_ROOT, "resume_versions", new_file_name)
                    
                    if p_type == "new":
                        content = copy.deepcopy(DEFAULT)
                    else:
                        content = copy.deepcopy(st.session_state.resume)
                        
                    # Save new profile to disk
                    with open(new_path, "w", encoding="utf-8") as f:
                        json.dump(content, f, indent=2)
                        
                    # Switch to new profile
                    st.session_state.current_profile_path = new_path
                    st.session_state.resume = content
                    st.session_state.last_hash = ""
                    st.session_state.show_create_profile = False
                    st.success(f"Profile '{clean_name}' created successfully!")
                    st.rerun()
            if cancel:
                st.session_state.show_create_profile = False
                st.rerun()

    # Show delete profile confirmation
    if st.session_state.get("show_delete_confirm", False):
        with st.form("delete_profile_form"):
            st.error(f"⚠️ Are you sure you want to delete the profile: **{selected_name}**?")
            st.write("This action cannot be undone and the file will be deleted permanently.")
            dfc1, dfc2 = st.columns(2)
            with dfc1:
                confirm_del = st.form_submit_button("Yes, Delete", use_container_width=True, type="primary")
            with dfc2:
                cancel_del = st.form_submit_button("Cancel", use_container_width=True)
                
            if confirm_del:
                path_to_delete = profiles[selected_name]
                if os.path.exists(path_to_delete) and selected_name != "Default Profile":
                    os.remove(path_to_delete)
                st.session_state.current_profile_path = os.path.join(PROJECT_ROOT, "resume.json")
                st.session_state.resume = load_from_disk()
                st.session_state.last_hash = ""
                st.session_state.show_delete_confirm = False
                st.success("Profile deleted successfully.")
                st.rerun()
            if cancel_del:
                st.session_state.show_delete_confirm = False
                st.rerun()

    st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)

    t_contact, t_exp, t_projects, t_skills, t_edu, t_settings = st.tabs([
        "👤 Contact", "💼 Experience", "🚀 Projects", "🛠️ Skills", "🎓 Education", "⚙️ Settings"
    ])

    # ── TAB 1: Contact ───────────────────────────────
    with t_contact:
        st.markdown(
            '<div class="tab-hint"><span class="th-icon">✏️</span>'
            'Fill in your <b>contact details and professional summary</b> here. '
            'Every change updates the preview instantly — no need to save first.</div>',
            unsafe_allow_html=True,
        )
        p = d.get("personal", {})

        st.markdown('<div class="sec-title">Personal Details</div>', unsafe_allow_html=True)
        cc1, cc2 = st.columns(2)
        with cc1:
            st.text_input("Full Name *",   p.get("name",""),     key="f_nm")
            st.text_input("Email *",       p.get("email",""),    key="f_em")
            st.text_input("Phone",         p.get("phone",""),    key="f_ph")
        with cc2:
            st.text_input("Location",      p.get("location",""), key="f_lc")
            lid = p.get("linkedin",{})
            st.text_input("LinkedIn Label",lid.get("display",""),key="f_lid")
            st.text_input("LinkedIn URL",  lid.get("url",""),    key="f_liu")

        gd = p.get("github",{})
        gc1, gc2 = st.columns(2)
        with gc1: st.text_input("GitHub Label", gd.get("display",""), key="f_ghd")
        with gc2: st.text_input("GitHub URL",   gd.get("url",""),     key="f_ghu")

        st.markdown('<div class="sec-title">Professional Summary</div>', unsafe_allow_html=True)
        st.caption("Recommended: 40–80 words · Your career focus & top strength.")
        st.text_area("Summary", d.get("summary",""), height=110,
                     label_visibility="collapsed", key="f_summ")

        # Add/Remove controls
        st.markdown('<div class="hdiv"></div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-title">Achievements</div>', unsafe_allow_html=True)
        st.caption("One achievement per line. Recommended: 3–5 items.")
        st.text_area("Achievements", "\n".join(d.get("achievements",[])),
                     height=90, label_visibility="collapsed", key="f_ach")

    # ── TAB 2: Experience ─────────────────────────────
    with t_exp:
        st.markdown(
            '<div class="tab-hint"><span class="th-icon">💼</span>'
            'Add each <b>job role</b> using the button below — list your most recent job first. '
            'Use one bullet point per line in the Bullets field.</div>',
            unsafe_allow_html=True,
        )
        ec1, ec2 = st.columns([1,1])
        with ec1:
            if st.button("➕ Add Job", key="add_exp", use_container_width=True):
                push_undo(d)
                d.setdefault("experience",[]).append(
                    {"role":"","company":"","location":"","period":"","technologies":"","bullets":[]})
                save_to_disk(d); st.session_state.resume = d; st.session_state.last_hash = ""; st.rerun()
        with ec2:
            if d.get("experience") and st.button("🗑 Remove Last", key="rm_exp", use_container_width=True):
                push_undo(d)
                d["experience"].pop()
                save_to_disk(d); st.session_state.resume = d; st.session_state.last_hash = ""; st.rerun()

        if not d.get("experience"):
            st.info("No experience added yet. Click **➕ Add Job** above.")
        for i, exp in enumerate(d.get("experience",[])):
            title   = exp.get("role","") or "New Role"
            company = exp.get("company","") or "Company"
            with st.expander(f"💼 {title} @ {company}", expanded=(i==0)):
                r1, r2 = st.columns(2)
                with r1:
                    st.text_input("Job Title",   exp.get("role",""),         key=f"f_er{i}")
                    st.text_input("Company",     exp.get("company",""),      key=f"f_ec{i}")
                with r2:
                    st.text_input("Location",    exp.get("location",""),     key=f"f_el{i}")
                    st.text_input("Duration",    exp.get("period",""),       key=f"f_ep{i}")
                st.text_input("Technologies",    exp.get("technologies",""), key=f"f_et{i}")
                st.text_area("Bullets (1 per line)", "\n".join(exp.get("bullets",[])),
                             height=88, key=f"f_eb{i}")

    # ── TAB 3: Projects ───────────────────────────────
    with t_projects:
        st.markdown(
            '<div class="tab-hint"><span class="th-icon">🚀</span>'
            'Add your <b>best projects</b> here. Paste a GitHub or live demo link, '
            'list the tools used, and describe what you built — one bullet per line. '
            'Tip: use the <b>💼 Career → GitHub Evidence</b> tool to import repos automatically.</div>',
            unsafe_allow_html=True,
        )
        pc1, pc2 = st.columns([1,1])
        with pc1:
            if st.button("➕ Add Project", key="add_proj", use_container_width=True):
                push_undo(d)
                d.setdefault("projects",[]).append(
                    {"title":"","link":"","date":"","tools":"","bullets":[]})
                save_to_disk(d); st.session_state.resume = d; st.session_state.last_hash = ""; st.rerun()
        with pc2:
            if d.get("projects") and st.button("🗑 Remove Last", key="rm_proj", use_container_width=True):
                push_undo(d)
                d["projects"].pop()
                save_to_disk(d); st.session_state.resume = d; st.session_state.last_hash = ""; st.rerun()

        if not d.get("projects"):
            st.info("No projects added yet. Click **➕ Add Project** above.")
        for i, pr in enumerate(d.get("projects",[])):
            title = pr.get("title","") or "New Project"
            with st.expander(f"🚀 {title}", expanded=(i==0)):
                r1, r2 = st.columns(2)
                with r1:
                    st.text_input("Title",  pr.get("title",""), key=f"f_pt{i}")
                    st.text_input("Link",   pr.get("link",""),  key=f"f_plk{i}")
                with r2:
                    st.text_input("Tools",  pr.get("tools",""), key=f"f_ptl{i}")
                    st.text_input("Date",   pr.get("date",""),  key=f"f_pdt{i}")
                st.text_area("Description (1 bullet per line)", "\n".join(pr.get("bullets",[])),
                             height=88, key=f"f_pb{i}")

    # ── TAB 4: Skills ─────────────────────────────────
    with t_skills:
        st.markdown(
            '<div class="tab-hint"><span class="th-icon">🛠️</span>'
            'Group your skills by <b>category</b> (e.g. Programming, Frontend, Tools). '
            'Edit existing categories or add a new one below, then click <b>➕ Add Skill</b>.</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="sec-title">Technical Skills</div>', unsafe_allow_html=True)
        sk = d.get("technical_skills",{})
        keys_list = list(sk.keys())
        sk_changed = False
        new_sk = {}
        for i, k in enumerate(keys_list):
            sc1, sc2, sc3 = st.columns([.30, .60, .10])
            with sc1: nk = st.text_input("Category", k, key=f"f_sk{i}")
            with sc2: nv = st.text_input("Skills",   sk[k], key=f"f_sv{i}")
            with sc3:
                st.markdown('<div style="margin-top:28px"></div>', unsafe_allow_html=True)
                if st.button("🗑", key=f"rm_sk{i}", help="Remove this skill category"):
                    push_undo(d)
                    new_sk_after_del = {kk: vv for j,(kk,vv) in enumerate(sk.items()) if j != i}
                    d["technical_skills"] = new_sk_after_del
                    save_to_disk(d); st.session_state.resume = d; st.session_state.last_hash = ""; st.rerun()
            if nk:
                new_sk[nk] = nv

        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
        st.markdown("**➕ Add new skill category:**")
        nc1, nc2, nc3 = st.columns([.30, .60, .10])
        with nc1: st.text_input("New Category", "", placeholder="e.g. Databases", key="f_ncat")
        with nc2: st.text_input("Skills",       "", placeholder="e.g. MySQL, MongoDB", key="f_nval")
        with nc3:
            st.markdown('<div style="margin-top:28px"></div>', unsafe_allow_html=True)
            if st.button("➕", key="add_sk_btn", help="Add this skill category"):
                ncat = st.session_state.get("f_ncat","").strip()
                nval = st.session_state.get("f_nval","").strip()
                if ncat:
                    push_undo(d)
                    live_sk = {}
                    for i2, k2 in enumerate(list(d.get("technical_skills",{}).keys())):
                        nk2 = st.session_state.get(f"f_sk{i2}", k2)
                        nv2 = st.session_state.get(f"f_sv{i2}", d["technical_skills"][k2])
                        if nk2: live_sk[nk2] = nv2
                    live_sk[ncat] = nval
                    d["technical_skills"] = live_sk
                    save_to_disk(d); st.session_state.resume = d; st.session_state.last_hash = ""
                    # Clear inputs
                    for k3 in ["f_ncat", "f_nval"]:
                        if k3 in st.session_state: del st.session_state[k3]
                    st.rerun()

    # ── TAB 5: Education & Positions ──────────────────
    with t_edu:
        st.markdown(
            '<div class="tab-hint"><span class="th-icon">🎓</span>'
            'Add your <b>degrees, institutions, and CGPA</b> here. '
            'You can also add positions of responsibility (clubs, committees) in the section below.</div>',
            unsafe_allow_html=True,
        )
        ec1, ec2 = st.columns(2)
        with ec1:
            if st.button("➕ Add Education", key="add_edu", use_container_width=True):
                push_undo(d)
                d.setdefault("education",[]).append(
                    {"degree":"","institution":"","details":"","period":""})
                save_to_disk(d); st.session_state.resume = d; st.rerun()
        with ec2:
            if d.get("education") and st.button("🗑 Remove Last", key="rm_edu", use_container_width=True):
                push_undo(d)
                d["education"].pop()
                save_to_disk(d); st.session_state.resume = d; st.rerun()

        if not d.get("education"):
            st.info("No education added yet.")
        for i, edu in enumerate(d.get("education",[])):
            dg = edu.get("degree","") or "Degree"
            sc = edu.get("institution","") or "Institution"
            with st.expander(f"🎓 {dg} — {sc}", expanded=(i==0)):
                r1, r2 = st.columns(2)
                with r1:
                    st.text_input("Degree",     edu.get("degree",""),      key=f"f_ed{i}")
                    st.text_input("Grade/CGPA", edu.get("details",""),     key=f"f_edd{i}")
                with r2:
                    st.text_input("Institution",edu.get("institution",""), key=f"f_ei{i}")
                    st.text_input("Year/Period", edu.get("period",""),     key=f"f_epp{i}")

        st.markdown('<div class="sec-title">Positions of Responsibility</div>', unsafe_allow_html=True)
        pr1, pr2 = st.columns(2)
        with pr1:
            if st.button("➕ Add Position", key="add_por", use_container_width=True):
                push_undo(d)
                d.setdefault("position_of_responsibility",[]).append(
                    {"role":"","period":"","bullets":[]})
                save_to_disk(d); st.session_state.resume = d; st.rerun()
        with pr2:
            if d.get("position_of_responsibility") and st.button("🗑 Remove Last", key="rm_por", use_container_width=True):
                push_undo(d)
                d["position_of_responsibility"].pop()
                save_to_disk(d); st.session_state.resume = d; st.rerun()
        for i, por in enumerate(d.get("position_of_responsibility",[])):
            role = por.get("role","") or "Position"
            with st.expander(f"🤝 {role}", expanded=(i==0)):
                r1, r2 = st.columns([.7,.3])
                with r1: st.text_input("Role & Organisation", por.get("role",""),   key=f"f_prr{i}")
                with r2: st.text_input("Period",              por.get("period",""), key=f"f_prp{i}")
                st.text_area("Bullets", "\n".join(por.get("bullets",[])),
                             height=72, key=f"f_prb{i}")

    # ── TAB 6: Settings ───────────────────────────────
    with t_settings:
        st.markdown(
            '<div class="tab-hint"><span class="th-icon">⚙️</span>'
            'Tweak <b>font size, margins, and page fitting</b> to make your resume fit perfectly on one page. '
            'Use <b>Auto Compress</b> to let the app squeeze everything automatically. '
            'Download the final PDF or JSON from the buttons below.</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="sec-title">Page Layout</div>', unsafe_allow_html=True)

        # Margins with explanation
        new_m = st.slider("Margin (pt)", 10, 36, M, 2, key="adv_mg")
        m_txt, m_cls = margin_label(new_m)
        st.markdown(f'Current: <b>{new_m}pt</b> → <span class="setting-effect {m_cls}">{m_txt}</span>',
                    unsafe_allow_html=True)

        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)

        # Font scale with explanation
        new_fs = st.slider("Font Scale", 0.75, 1.25, FS, 0.05, key="adv_fs")
        fs_txt, fs_cls = fscale_label(new_fs)
        st.markdown(f'Current: <b>{new_fs:.2f}×</b> → <span class="setting-effect {fs_cls}">{fs_txt}</span>',
                    unsafe_allow_html=True)

        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)

        # Page fitting
        st.markdown('<div class="sec-title">Page Fitting</div>', unsafe_allow_html=True)
        new_ft = st.radio("Page Fitting", FITTING_OPTS,
                          index=FITTING_OPTS.index(FT),
                          key="adv_fit", label_visibility="collapsed",
                          horizontal=True)

        # Apply settings — force rerun so maybe_compile picks up new values
        changed_settings = (new_m != M) or (new_fs != FS) or (new_ft != FT)
        if changed_settings:
            st.session_state.margins = new_m
            st.session_state.fscale  = new_fs
            st.session_state.fitting = new_ft
            st.session_state.last_hash = ""
            st.rerun()

        st.markdown('<div class="sec-title">Save & Download</div>', unsafe_allow_html=True)

        # Manual save button (always available)
        if st.button("💾 Save to File", key="manual_save", use_container_width=True, type="primary"):
            live = collect_resume()
            push_undo(st.session_state.resume)
            st.session_state.resume = live
            save_to_disk(live)
            st.session_state.last_hash = ""
            st.success("✅ Saved!")
            st.rerun()

        # Download buttons
        pname = d.get("personal",{}).get("name","Resume")
        safe  = re.sub(r"[^a-zA-Z0-9]","_",pname).strip("_") or "Resume"
        if st.session_state.cok and st.session_state.pdf_raw:
            dl1, dl2 = st.columns(2)
            with dl1:
                st.download_button("📥 PDF",
                    data=st.session_state.pdf_raw,
                    file_name=f"{safe}_Resume.pdf",
                    mime="application/pdf",
                    use_container_width=True, type="primary", key="dl_pdf")
            with dl2:
                st.download_button("📋 JSON",
                    data=json.dumps(st.session_state.resume, indent=2).encode(),
                    file_name="resume_data.json",
                    mime="application/json",
                    use_container_width=True, key="dl_json")

        with st.expander("🌐 Web Portfolio", expanded=False):
            try:
                from resume_builder.portfolio import exporter as pe
                if st.button("Generate Portfolio HTML", key="port_gen", use_container_width=True):
                    with st.spinner("Generating…"):
                        hc = pe.generate_portfolio_html(d, C)
                        os.makedirs(os.path.join("resume_builder","exports","html"), exist_ok=True)
                        hp = os.path.join("resume_builder","exports","html","index.html")
                        with open(hp,"w",encoding="utf-8") as hf: hf.write(hc)
                        st.download_button("📥 Download index.html", data=hc.encode(),
                                           file_name="index.html", mime="text/html",
                                           use_container_width=True, key="dl_port")
            except Exception as ex:
                st.error(f"Portfolio error: {ex}")


# ─────────────────────────────────────────────────────
# LIVE COLLECTION — detect changes, update state, auto-compile
# ─────────────────────────────────────────────────────
live = collect_resume()

# Deep compare: only push undo when the actual resume dict changes
# (not on tab switches, scrolls, or non-content reruns)
if live != st.session_state.resume:
    push_undo(st.session_state.resume)
    st.session_state.resume = live
    st.session_state.last_hash = ""   # force PDF recompile
    save_to_disk(live)

d   = st.session_state.resume
C   = st.session_state.color
M   = st.session_state.margins
FS  = st.session_state.fscale
FT  = st.session_state.fitting
TID = st.session_state.template


# ─────────────────────────────────────────────────────
# RIGHT PANEL — Sticky Live Preview
# ─────────────────────────────────────────────────────
with right_col:
    # Make the right column sticky via precise CSS injection (desktop only)
    st.markdown('<div id="right-panel-anchor"></div>', unsafe_allow_html=True)
    st.markdown("""
    <style>
    @media (min-width: 768px) {
      /* Sticky right column targeting specifically the parent column */
      [data-testid="column"]:has(#right-panel-anchor) {
        position: sticky;
        top: 2rem;
        align-self: flex-start;
        /* Custom scrollbar for sticky element if it overflows vertically */
        max-height: calc(100vh - 4rem);
        overflow-y: auto;
      }
      [data-testid="column"]:has(#right-panel-anchor)::-webkit-scrollbar { width: 6px; }
      [data-testid="column"]:has(#right-panel-anchor)::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 10px; }
    }
    </style>
    """, unsafe_allow_html=True)

    # Compile badge + health score row
    hs  = calculate_health_score(d)
    h_col = "c-green" if hs["score"]>=80 else ("c-amber" if hs["score"]>=50 else "c-red")

    pr1, pr2, pr3 = st.columns(3)
    with pr1:
        st.markdown(
            f'<div class="kpi"><div class="kpi-lbl">HEALTH SCORE</div>'
            f'<div class="kpi-val {h_col}">{hs["score"]}%</div></div>',
            unsafe_allow_html=True)
    with pr2:
        status_icon = "✅" if st.session_state.cok else "⏳"
        status_txt  = "Ready" if st.session_state.cok else "Compiling…"
        st.markdown(
            f'<div class="kpi"><div class="kpi-lbl">PDF STATUS</div>'
            f'<div class="kpi-val" style="font-size:1.4rem;">{status_icon} {status_txt}</div></div>',
            unsafe_allow_html=True)
    with pr3:
        tname_disp = ALL_TEMPLATES.get(TID,{}).get("name",TID)
        st.markdown(
            f'<div class="kpi"><div class="kpi-lbl">TEMPLATE</div>'
            f'<div class="kpi-val" style="font-size:.85rem;line-height:1.3;">{tname_disp}</div></div>',
            unsafe_allow_html=True)

    # Auto-compile (always on)
    with st.spinner("🔄 Updating preview…"):
        try:
            maybe_compile(d, TID, C, M, FS, FT)
        except Exception as compile_err:
            st.session_state.cok = False
            st.session_state.cmsg = f"Compilation error: {compile_err}"

    # Compile message
    if st.session_state.cmsg:
        st.warning(f"⚠️ {st.session_state.cmsg}")

    # PDF Viewer — auto-resizing + clickable links
    if st.session_state.cok and st.session_state.pdf_b64:
        pdf_b64 = st.session_state.pdf_b64
        pdf_html = f"""<!DOCTYPE html>
<html>
<head>
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.min.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{
    background: #F0F2F8;
    overflow-x: hidden;
    width: 100%;
  }}
  #pages-container {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    width: 100%;
    padding: 6px 4px 10px 4px;
  }}
  .page-wrapper {{
    position: relative;
    display: inline-block;
    max-width: 100%;
    line-height: 0;
    border-radius: 3px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.18);
    background: #fff;
  }}
  .page-wrapper canvas {{
    display: block;
    width: 100%;
    height: auto !important;
    border-radius: 3px;
  }}
  .link-overlay {{
    position: absolute;
    cursor: pointer;
    z-index: 10;
  }}
  ::-webkit-scrollbar {{ width: 5px; }}
  ::-webkit-scrollbar-thumb {{ background: #CBD5E1; border-radius: 10px; }}
</style>
</head>
<body>
<div id="pages-container"></div>
<script>
  const pdfjsLib = window['pdfjs-dist/build/pdf'];
  pdfjsLib.GlobalWorkerOptions.workerSrc =
    'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';

  const base64PDF = "{pdf_b64}";

  function b64ToArr(b64) {{
    const raw = atob(b64);
    const arr = new Uint8Array(raw.length);
    for (let i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
    return arr;
  }}

  function sendHeight() {{
    const h = Math.max(
      document.body.scrollHeight,
      document.documentElement.scrollHeight
    ) + 24;
    window.parent.postMessage({{ type: 'streamlit:setFrameHeight', height: h }}, '*');
  }}

  pdfjsLib.getDocument({{ data: b64ToArr(base64PDF) }}).promise.then(async (pdf) => {{
    const container = document.getElementById('pages-container');
    const SCALE = 2.0;

    for (let p = 1; p <= pdf.numPages; p++) {{
      const page   = await pdf.getPage(p);
      const vp     = page.getViewport({{ scale: SCALE }});

      // Wrapper div (relative position for link overlays)
      const wrapper = document.createElement('div');
      wrapper.className = 'page-wrapper';
      wrapper.style.maxWidth = (vp.width / SCALE) + 'px';
      wrapper.style.width = '100%';

      // Canvas
      const canvas = document.createElement('canvas');
      const ctx    = canvas.getContext('2d');
      canvas.height = vp.height;
      canvas.width  = vp.width;
      wrapper.appendChild(canvas);

      // Render PDF page onto canvas
      await page.render({{ canvasContext: ctx, viewport: vp }}).promise;

      // --- Clickable link overlays ---
      const annotations = await page.getAnnotations();
      for (const annot of annotations) {{
        if (annot.subtype !== 'Link') continue;
        const url = annot.url || (annot.action && annot.action.url);
        if (!url) continue;

        // Convert PDF rect [x1,y1,x2,y2] to viewport coordinates
        const [x1, y1, x2, y2] = vp.convertToViewportRectangle(annot.rect);
        const left   = Math.min(x1, x2);
        const top    = Math.min(y1, y2);
        const width  = Math.abs(x2 - x1);
        const height = Math.abs(y2 - y1);

        // Express as % of canvas dimensions so it scales with CSS width
        const a = document.createElement('a');
        a.href   = url;
        a.target = '_blank';
        a.rel    = 'noopener noreferrer';
        a.className = 'link-overlay';
        a.style.left   = (left   / vp.width  * 100) + '%';
        a.style.top    = (top    / vp.height * 100) + '%';
        a.style.width  = (width  / vp.width  * 100) + '%';
        a.style.height = (height / vp.height * 100) + '%';
        wrapper.appendChild(a);
      }}

      container.appendChild(wrapper);
    }}

    // Let DOM settle then report height
    setTimeout(sendHeight, 150);
  }}).catch(err => {{
    console.error('PDF render error:', err);
    document.getElementById('pages-container').innerHTML =
      '<div style="color:#c0392b;padding:20px;text-align:center;font-size:13px;">&#9888;&#65039; Failed to render PDF preview.<br>Use the Download button below.</div>';
    setTimeout(sendHeight, 100);
  }});
</script>
</body>
</html>"""
        import streamlit.components.v1 as components
        components.html(pdf_html, height=750, scrolling=True)

        # Quick download row
        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
        pname = d.get("personal",{}).get("name","Resume")
        safe  = re.sub(r"[^a-zA-Z0-9]","_",pname).strip("_") or "Resume"
        qd1, qd2 = st.columns(2)
        with qd1:
            st.download_button("📥 Download PDF",
                data=st.session_state.pdf_raw,
                file_name=f"{safe}_Resume.pdf",
                mime="application/pdf",
                use_container_width=True, type="primary", key="qd_pdf")
        with qd2:
            st.download_button("📋 Download JSON",
                data=json.dumps(d, indent=2).encode(),
                file_name="resume_data.json",
                mime="application/json",
                use_container_width=True, key="qd_json")

        # Suggestions
        if hs.get("suggestions"):
            with st.expander("💡 Improvement Tips", expanded=False):
                for s in hs["suggestions"][:5]:
                    st.markdown(f"- {s}")
    else:
        st.markdown("""
        <div class="preview-card" style="display:flex;flex-direction:column;
          align-items:center;justify-content:center;min-height:480px;gap:12px;">
          <div style="font-size:3.5rem;">📄</div>
          <div style="font-size:.95rem;color:#64748B;font-weight:500;text-align:center;">
            Your live resume preview will appear here.<br>
            <span style="font-size:.8rem;color:#94A3B8;">
            Edits on the left update automatically.</span>
          </div>
        </div>""", unsafe_allow_html=True)
        if st.session_state.cmsg:
            st.error(f"❌ {st.session_state.cmsg}")

# ═══════════════════════════════════════════════════════
# KEYBOARD SHORTCUTS (Ctrl+Z / Ctrl+Y / Ctrl+S)
# ═══════════════════════════════════════════════════════
st.markdown("""
<script>
const parentDoc = window.parent.document;
parentDoc.addEventListener('keydown', function(e) {
    // Ctrl+Z: Undo
    if (e.ctrlKey && !e.shiftKey && e.key.toLowerCase() === 'z') {
        e.preventDefault();
        const buttons = parentDoc.querySelectorAll('button');
        for (const btn of buttons) {
            if (btn.innerText.trim() === '↩' && !btn.disabled) {
                btn.click();
                break;
            }
        }
    }
    // Ctrl+Y / Ctrl+Shift+Z: Redo
    if ((e.ctrlKey && e.key.toLowerCase() === 'y') || (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'z')) {
        e.preventDefault();
        const buttons = parentDoc.querySelectorAll('button');
        for (const btn of buttons) {
            if (btn.innerText.trim() === '↪' && !btn.disabled) {
                btn.click();
                break;
            }
        }
    }
    // Ctrl+S: Save
    if (e.ctrlKey && e.key.toLowerCase() === 's') {
        e.preventDefault();
        const buttons = parentDoc.querySelectorAll('button');
        for (const btn of buttons) {
            if (btn.innerText.trim().includes('Save to File') && !btn.disabled) {
                btn.click();
                break;
            }
        }
    }
});
</script>
""", unsafe_allow_html=True)
