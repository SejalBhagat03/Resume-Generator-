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
from resume_builder.career_dashboard import show_career_center


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

/* Base - force light theme */
html, body, [data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section,
[data-testid="stVerticalBlock"],
.main .block-container {
  font-family: 'Inter', sans-serif !important;
  background: #F8FAFC !important;
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

/* Modern App Padding */
.block-container {
  padding: 0.5rem 2rem 75px !important; /* Compact bottom padding for fixed bar */
  max-width: 1600px !important;
}
[data-testid="stAppViewContainer"] > .main { padding: 0 !important; }

/* Light Premium Top Bar Toolbar */
div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] {
  background: #FFFFFF !important;
  padding: 12px 20px !important;
  border-radius: 20px !important;
  border: 1px solid #E2E8F0 !important;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03) !important;
  margin-bottom: 12px !important;
  align-items: center !important;
}

/* Style selectboxes inside the top bar */
div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] .stSelectbox div[data-baseweb="select"] > div {
  border-radius: 20px !important;
  border: 1px solid #E2E8F0 !important;
  background-color: #FFFFFF !important;
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

/* Active navigation button styling */
div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] button[kind="primary"] {
  background: #EEF2FF !important;
  color: #6366F1 !important;
  border: none !important;
  border-radius: 20px !important;
  box-shadow: none !important;
}
div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] button[kind="secondary"] {
  background: #FFFFFF !important;
  color: #475569 !important;
  border: 1px solid #E2E8F0 !important;
  border-radius: 20px !important;
}
div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] button:hover:not(:disabled) {
  background-color: #F8FAFC !important;
  border-color: #CBD5E1 !important;
  color: #1E293B !important;
}
div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] button:disabled {
  opacity: 0.5 !important;
  color: #94A3B8 !important;
}

/* Actions Dropdown custom styling (7th column) */
div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(7) .stSelectbox div[data-baseweb="select"] > div {
  border: 1px solid #6366F1 !important;
  background-color: #FFFFFF !important;
  color: #6366F1 !important;
  border-radius: 20px !important;
}
div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(7) .stSelectbox span {
  color: #6366F1 !important;
  font-weight: 600 !important;
}
div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(7) .stSelectbox svg {
  fill: #6366F1 !important;
}

/* User Profile custom styling (8th column) */
div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(8) .stSelectbox div[data-baseweb="select"] > div {
  border: none !important;
  background-color: #EEF2FF !important;
  border-radius: 20px !important;
}
div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(8) .stSelectbox span {
  color: #6366F1 !important;
  font-weight: 600 !important;
}
div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(8) .stSelectbox svg {
  fill: #6366F1 !important;
}

/* Custom styling for color picker block inside top bar */
div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] div[data-testid="stColorPickerColorBlock"] {
  border-radius: 8px !important;
  border: 1px solid #E2E8F0 !important;
}
div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] .stColorPicker > div {
  margin-top: -6px !important;
}

/* Sticky preview card */
.preview-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0,0,0,.12);
  overflow: hidden;
  min-height: 600px;
}

/* Section headers inside form */
.sec-title {
  font-size: .78rem; font-weight: 700; color: #6366F1;
  text-transform: uppercase; letter-spacing: .08em;
  margin: 10px 0 6px; padding-bottom: 3px;
  border-bottom: 2px solid #EEF2FF;
}

/* Setting row with explanation */
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

/* Undo/Redo pill buttons */
.ur-btn {
  display: inline-flex; align-items: center; justify-content: center;
  width: 32px; height: 32px; border-radius: 8px;
  background: rgba(255,255,255,.12); color: #fff; font-size: .9rem;
  cursor: pointer; border: 1px solid rgba(255,255,255,.2);
  transition: background .15s;
}
.ur-btn:hover { background: rgba(255,255,255,.22); }
.ur-btn.disabled { opacity: .35; cursor: not-allowed; }

/* Streamlit widget overrides */
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

/* Onboarding Banner */
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

/* Tab Hint Chips */
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

/* Home Dashboard Hero Cards */
.hero-card {
  background: #FFFFFF;
  border: 1.5px solid #E2E8F0;
  border-radius: 20px;
  padding: 32px 24px 28px;
  text-align: center;
  cursor: pointer;
  transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.2s ease;
  min-height: 220px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
}
.hero-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 20px 40px rgba(99,102,241,.15);
  border-color: #A5B4FC;
}
.hero-card.build { border-top: 4px solid #6366F1; }
.hero-card.import { border-top: 4px solid #10B981; }
.hero-card.career { border-top: 4px solid #F59E0B; }
.hero-icon {
  font-size: 3rem;
  line-height: 1;
}
.hero-title {
  font-size: 1.25rem;
  font-weight: 800;
  color: #1E293B;
  letter-spacing: -.02em;
  margin: 0;
}
.hero-desc {
  font-size: 0.84rem;
  color: #64748B;
  line-height: 1.5;
  margin: 0;
}

/* Sub-header Progress Card Styling */
div:has(#sub-header-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] {
  background: #FFFFFF !important;
  border-radius: 16px !important;
  border: 1px solid #E2E8F0 !important;
  padding: 12px 20px !important;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03) !important;
  margin-bottom: 12px !important;
  align-items: center !important;
  position: relative !important;
}
div:has(#sub-header-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"]::before {
  content: "" !important;
  position: absolute !important;
  top: 33px !important;
  left: 42% !important;
  width: 50% !important;
  height: 2px !important;
  background: #F1F5F9 !important;
  z-index: 0 !important;
}
div:has(#sub-header-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(n+3) button {
  width: 42px !important;
  height: 42px !important;
  min-width: 42px !important;
  border-radius: 50% !important;
  padding: 0 !important;
  margin: 0 auto !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  font-size: 0.95rem !important;
  font-weight: 700 !important;
  z-index: 1 !important;
  position: relative !important;
}
div:has(#sub-header-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(n+3) button[kind="primary"] {
  background: #6366F1 !important;
  color: #FFFFFF !important;
  border: none !important;
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.2) !important;
}
div:has(#sub-header-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(n+3) button[kind="secondary"] {
  background: #F8FAFC !important;
  color: #64748B !important;
  border: 1px solid #E2E8F0 !important;
}
.step-label {
  font-size: 0.72rem !important;
  font-weight: 600 !important;
  color: #64748B;
  text-align: center;
  margin-top: 6px;
  white-space: nowrap;
}
.step-label.active {
  color: #6366F1 !important;
  font-weight: 700 !important;
}

/* Fixed Bottom Actions Bar */
div:has(#bottom-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] {
  position: fixed !important;
  bottom: 0 !important;
  left: 0 !important;
  right: 0 !important;
  background: #FFFFFF !important;
  border-top: 1px solid #E2E8F0 !important;
  padding: 12px 64px !important;
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.05) !important;
  z-index: 999999 !important;
  margin: 0 !important;
  align-items: center !important;
}
div:has(#bottom-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] button {
  border-radius: 20px !important;
  height: 38px !important;
  font-weight: 600 !important;
  font-size: 0.85rem !important;
}
div:has(#bottom-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] button[kind="primary"] {
  background: #6366F1 !important;
  color: #FFFFFF !important;
  border: none !important;
  box-shadow: 0 2px 8px rgba(99,102,241,.3) !important;
}
div:has(#bottom-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] button[kind="secondary"] {
  background: #FFFFFF !important;
  color: #475569 !important;
  border: 1px solid #E2E8F0 !important;
}
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
    "achievements": [], "certifications": [], "education": [], "position_of_responsibility": [],
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
    "certifications": [
        "AWS Certified Cloud Practitioner"
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
_s("navigation_page", "home")
# Import wizard
_s("show_import", False)
_s("wiz_step",    "upload")
_s("wiz_blk",     [])
_s("wiz_lay",     None)
# Editor wizard step (0=Basic, 1=Education, 2=Experience, 3=Projects, 4=Skills, 5=Finish)
_s("editor_step", 0)
# Profile versions manager
_s("show_create_profile", False)
_s("create_profile_type", "new")
_s("show_delete_confirm", False)
_s("show_profile",        False)


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
    if "metadata" not in d:
        d["metadata"] = {}
    meta = d["metadata"]
    
    # Sync current UI configuration to metadata on save
    meta["template"] = st.session_state.get("template", meta.get("template", "sejal_original"))
    meta["color"] = st.session_state.get("color", meta.get("color", "#6366F1"))
    meta["margins"] = st.session_state.get("margins", meta.get("margins", 20))
    meta["fscale"] = st.session_state.get("fscale", meta.get("fscale", 1.0))
    meta["fitting"] = st.session_state.get("fitting", meta.get("fitting", FITTING_OPTS[0]))
    meta["last_edited"] = time.time()
    
    with open(get_profile_path(), "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)
    _read_json.clear()

def load_from_disk() -> dict:
    return _read_json(get_profile_path())

def load_active_resume(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            resume = json.load(f)
    except Exception:
        resume = copy.deepcopy(DEFAULT)
        
    if "metadata" not in resume:
        resume["metadata"] = {}
    meta = resume["metadata"]
    
    # Ensure title is present
    if not meta.get("title"):
        if os.path.abspath(path) == os.path.abspath(os.path.join(PROJECT_ROOT, "resume.json")):
            meta["title"] = "Default Resume"
        else:
            base = os.path.splitext(os.path.basename(path))[0]
            meta["title"] = base.replace("_", " ").title()
            
    # Set session state from metadata
    st.session_state.current_profile_path = path
    st.session_state.resume = resume
    st.session_state.template = meta.get("template", "sejal_original")
    st.session_state.color = meta.get("color", "#6366F1")
    st.session_state.margins = meta.get("margins", 20)
    st.session_state.fscale = meta.get("fscale", 1.0)
    st.session_state.fitting = meta.get("fitting", FITTING_OPTS[0])
    
    # Update last_edited if missing
    meta["last_edited"] = meta.get("last_edited", os.path.getmtime(path) if os.path.exists(path) else time.time())
    
    # Write back to file to save initialized values
    with open(path, "w", encoding="utf-8") as f:
        json.dump(resume, f, indent=2)
    _read_json.clear()
    
    st.session_state.last_hash = "" # force compile

def list_resumes() -> list:
    resumes = []
    # 1. Check root resume.json
    root_path = os.path.join(PROJECT_ROOT, "resume.json")
    if os.path.exists(root_path):
        try:
            with open(root_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            meta = data.get("metadata", {})
            mtime = os.path.getmtime(root_path)
            last_edited = meta.get("last_edited", mtime)
            title = meta.get("title") or data.get("personal", {}).get("name") or "Default Resume"
            template = meta.get("template") or "sejal_original"
            resumes.append({
                "title": title,
                "path": root_path,
                "last_edited": last_edited,
                "template": template,
                "color": meta.get("color", "#6366F1")
            })
        except Exception:
            pass
            
    # 2. Check resume_versions/
    versions_dir = os.path.join(PROJECT_ROOT, "resume_versions")
    if os.path.exists(versions_dir):
        for fname in os.listdir(versions_dir):
            if fname.endswith(".json"):
                fpath = os.path.join(versions_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    meta = data.get("metadata", {})
                    mtime = os.path.getmtime(fpath)
                    last_edited = meta.get("last_edited", mtime)
                    title = meta.get("title") or os.path.splitext(fname)[0].replace("_", " ").title()
                    template = meta.get("template") or "sejal_original"
                    resumes.append({
                        "title": title,
                        "path": fpath,
                        "last_edited": last_edited,
                        "template": template,
                        "color": meta.get("color", "#6366F1")
                    })
                except Exception:
                    pass
    # Sort by last_edited descending
    resumes.sort(key=lambda r: r["last_edited"], reverse=True)
    return resumes

@st.cache_data(show_spinner=False)
def load_local_pdfjs_assets() -> tuple:
    static_dir = os.path.join(PROJECT_ROOT, "resume_builder", "data", "static")
    js_path = os.path.join(static_dir, "pdf.min.js")
    worker_path = os.path.join(static_dir, "pdf.worker.min.js")
    
    # Check if files exist. If not, download them dynamically
    if not os.path.exists(js_path) or not os.path.exists(worker_path):
        os.makedirs(static_dir, exist_ok=True)
        import urllib.request
        try:
            urllib.request.urlretrieve("https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.min.js", js_path)
            urllib.request.urlretrieve("https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js", worker_path)
        except Exception:
            pass
            
    # Read files and return base64
    try:
        with open(js_path, "rb") as f:
            js_b64 = base64.b64encode(f.read()).decode("utf-8")
        with open(worker_path, "rb") as f:
            worker_b64 = base64.b64encode(f.read()).decode("utf-8")
        return js_b64, worker_b64
    except Exception:
        return "", ""


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
    # Safety protection bypass: if profile is locked, do not read inputs or update content
    if st.session_state.resume.get("metadata", {}).get("locked", False):
        return st.session_state.resume

    ss = st.session_state
    d  = st.session_state.resume   # fallback for missing keys

    def g(key, fallback=""):
        return sanitize_html(ss.get(key, fallback))

    # personal
    raw_li = ss.get("f_li", d.get("personal",{}).get("linkedin",{}).get("display",""))
    url_li = raw_li
    if url_li and not url_li.startswith(("http://", "https://")):
        url_li = "https://" + url_li
        
    raw_gh = ss.get("f_gh", d.get("personal",{}).get("github",{}).get("display",""))
    url_gh = raw_gh
    if url_gh and not url_gh.startswith(("http://", "https://")):
        url_gh = "https://" + url_gh

    raw_port = ss.get("f_port", d.get("personal",{}).get("portfolio",{}).get("display",""))
    url_port = raw_port
    if url_port and not url_port.startswith(("http://", "https://")):
        url_port = "https://" + url_port

    personal = {
        "name":     g("f_nm",  d.get("personal",{}).get("name","")),
        "title":    g("f_title", d.get("personal",{}).get("title","")),
        "email":    g("f_em",  d.get("personal",{}).get("email","")),
        "phone":    g("f_ph",  d.get("personal",{}).get("phone","")),
        "location": g("f_lc",  d.get("personal",{}).get("location","")),
        "linkedin": {
            "display": sanitize_html(raw_li),
            "url":     sanitize_html(url_li),
        },
        "github": {
            "display": sanitize_html(raw_gh),
            "url":     sanitize_html(url_gh),
        },
        "portfolio": {
            "display": sanitize_html(raw_port),
            "url":     sanitize_html(url_port),
        }
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

    # certifications
    certl_raw = g("f_cert", "\n".join(d.get("certifications",[])))
    certifications = [c.strip() for c in certl_raw.split("\n") if c.strip()]

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

    res = {
        "personal": personal,
        "summary": summary,
        "experience": exp_data,
        "projects": proj_data,
        "technical_skills": sk_data,
        "achievements": achievements,
        "certifications": certifications,
        "education": edu_data,
        "position_of_responsibility": por_data,
    }
    if "metadata" in d:
        res["metadata"] = d["metadata"]
    return res

def calculate_completion_status(d: dict) -> tuple:
    status = {}
    score = 0
    
    # 1. Profile / Basic Info (Name, Email, Phone)
    p = d.get("personal", {})
    if p.get("name") and p.get("email") and p.get("phone"):
        status["profile"] = ("Basic Information", "green")
        score += 20
    elif p.get("name") or p.get("email"):
        status["profile"] = ("Basic Information (incomplete)", "orange")
        score += 10
    else:
        status["profile"] = ("Basic Information", "red")
        
    # 2. Education
    edu = d.get("education", [])
    if edu and any(e.get("degree") and e.get("institution") for e in edu):
        status["education"] = ("Education", "green")
        score += 15
    else:
        status["education"] = ("Education", "red")
        
    # 3. Experience
    exp = d.get("experience", [])
    if exp and any(e.get("role") and e.get("company") for e in exp):
        status["experience"] = ("Experience", "green")
        score += 20
    elif exp:
        status["experience"] = ("Experience (incomplete)", "orange")
        score += 10
    else:
        status["experience"] = ("Experience", "red")
        
    # 4. Projects
    proj = d.get("projects", [])
    if proj and any(p.get("title") for p in proj):
        status["projects"] = ("Projects", "green")
        score += 15
    else:
        status["projects"] = ("Projects", "red")
        
    # 5. Skills
    skills = d.get("technical_skills", {})
    if skills and any(v.strip() for v in skills.values()):
        status["skills"] = ("Skills", "green")
        score += 15
    else:
        status["skills"] = ("Skills", "red")
        
    # 6. Certifications
    certs = d.get("certifications", [])
    if certs and any(c.strip() for c in certs):
        status["certifications"] = ("Certifications", "green")
        score += 7.5
    else:
        status["certifications"] = ("Certifications", "red")
        
    # 7. Achievements
    ach = d.get("achievements", [])
    if ach and any(a.strip() for a in ach):
        status["achievements"] = ("Achievements", "green")
        score += 7.5
    else:
        status["achievements"] = ("Achievements", "red")
        
    return int(score), status

# ═══════════════════════════════════════════════════════
# ① TOP BAR / EDITOR HEADER
# ═══════════════════════════════════════════════════════
st.markdown('<div id="top-bar-marker"></div>', unsafe_allow_html=True)

page = st.session_state.navigation_page

if page == "workspace":
    # Set default workspace tab
    if "workspace_tab" not in st.session_state:
        st.session_state.workspace_tab = "Edit"
        
    c_back, c_title, c_saved, c_edit, c_prev, c_ins, c_accent, c_user = st.columns(
        [1.3, 2.7, 0.8, 0.8, 0.9, 1.0, 1.2, 0.8], gap="small"
    )
    
    with c_back:
        if st.button("← Resumes", key="btn_back_home", use_container_width=True, help="Back to My Resumes"):
            st.session_state.navigation_page = "home"
            st.rerun()
            
    with c_title:
        ct_col1, ct_col2 = st.columns([8.2, 1.8])
        current_title = d.get("metadata", {}).get("title", "Untitled Resume")
        with ct_col1:
            new_title = st.text_input(
                "Resume Title",
                value=current_title,
                key="active_resume_title_input",
                label_visibility="collapsed",
                placeholder="Rename Resume"
            )
            if new_title.strip() and new_title.strip() != current_title:
                d["metadata"]["title"] = new_title.strip()
                save_to_disk(d)
                st.rerun()
        with ct_col2:
            with st.popover("⚙️", use_container_width=True, help="Resume options"):
                st.markdown("**Resume Options**")
                
                # Duplicate action
                if st.button("Duplicate", key="top_dup_btn", use_container_width=True):
                    base_name = os.path.splitext(os.path.basename(get_profile_path()))[0]
                    new_path = os.path.join(PROJECT_ROOT, "resume_versions", f"{base_name}_copy.json")
                    counter = 1
                    while os.path.exists(new_path):
                        new_path = os.path.join(PROJECT_ROOT, "resume_versions", f"{base_name}_copy_{counter}.json")
                        counter += 1
                    with open(get_profile_path(), "r", encoding="utf-8") as f:
                        content = json.load(f)
                    if "metadata" not in content:
                        content["metadata"] = {}
                    content["metadata"]["title"] = f"{current_title} Copy"
                    content["metadata"]["last_edited"] = time.time()
                    with open(new_path, "w", encoding="utf-8") as f:
                        json.dump(content, f, indent=2)
                    
                    load_active_resume(new_path)
                    st.session_state.editor_step = 0
                    st.rerun()
                    
                # Delete action
                is_root = (os.path.abspath(get_profile_path()) == os.path.abspath(os.path.join(PROJECT_ROOT, "resume.json")))
                if st.button("🗑️ Delete", key="top_del_btn", use_container_width=True, disabled=is_root, help="Root resume cannot be deleted"):
                    if os.path.exists(get_profile_path()):
                        os.remove(get_profile_path())
                    st.session_state.current_profile_path = os.path.join(PROJECT_ROOT, "resume.json")
                    st.session_state.resume = load_from_disk()
                    st.session_state.navigation_page = "home"
                    st.rerun()
            
    with c_saved:
        st.markdown(
            '<div style="height: 38px; display: flex; align-items: center; justify-content: center; color: #10B981; font-weight: 600; font-size: 0.78rem;">'
            'Saved ✓</div>',
            unsafe_allow_html=True
        )
        
    with c_edit:
        is_active_edit = (st.session_state.workspace_tab == "Edit")
        if st.button("✏️ Edit", key="btn_wtab_edit", type="primary" if is_active_edit else "secondary", use_container_width=True):
            st.session_state.workspace_tab = "Edit"
            st.rerun()
            
    with c_prev:
        is_active_prev = (st.session_state.workspace_tab == "Preview")
        if st.button("👁️ Preview", key="btn_wtab_prev", type="primary" if is_active_prev else "secondary", use_container_width=True):
            st.session_state.workspace_tab = "Preview"
            st.rerun()
            
    with c_ins:
        is_active_ins = (st.session_state.workspace_tab == "Insights")
        if st.button("📊 Insights", key="btn_wtab_ins", type="primary" if is_active_ins else "secondary", use_container_width=True):
            st.session_state.workspace_tab = "Insights"
            st.rerun()
            
    with c_accent:
        COLOR_ICONS = {
            "Indigo": "🔵 Indigo",
            "Blue": "🔵 Blue",
            "Emerald": "🟢 Emerald",
            "Rose": "🔴 Rose",
            "Violet": "🟣 Violet",
            "Slate": "⚫ Slate",
            "Custom": "🎨 Custom"
        }
        accent_options = list(ACCENT_PRESETS.keys()) + ["Custom"]
        cur_accent = next((n for n, v in ACCENT_PRESETS.items() if v == C), "Custom")
        sel_accent = st.selectbox(
            "Accent",
            options=accent_options,
            index=accent_options.index(cur_accent),
            format_func=lambda x: COLOR_ICONS.get(x, x),
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
            save_to_disk(d)
            st.rerun()
            
    with c_user:
        pname = d.get("personal", {}).get("name", "User")
        first_char = pname[0].upper() if pname else "U"
        st.markdown(
            f'<div style="width: 38px; height: 38px; background: #6366F1; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.95rem; margin: 0 auto; box-shadow: 0 2px 4px rgba(99,102,241,0.2);">'
            f'{first_char}</div>',
            unsafe_allow_html=True
        )

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
    load_active_resume(os.path.join(PROJECT_ROOT, "resume.json"))
    st.session_state.resume_loaded = True


# Re-evaluate session state variables to ensure they are fresh after load
d  = st.session_state.resume
C  = st.session_state.color
M  = st.session_state.margins
FS = st.session_state.fscale
FT = st.session_state.fitting
TID = st.session_state.template

# Routing check immediately stops the page if we are on My Resumes Home
if st.session_state.navigation_page in ("dashboard", "home"):
    show_home()
    st.stop()

if st.session_state.navigation_page == "career":
    st.session_state.navigation_page = "workspace"
    st.session_state.workspace_tab = "Insights"
    st.rerun()


@st.dialog("Import Resume")
def show_import_dialog():
    st.markdown("Upload your existing resume (PDF, DOCX, or TXT) to extract its structure and text details.")
    
    if "wiz_step" not in st.session_state:
        st.session_state.wiz_step = "upload"
        
    if st.session_state.wiz_step == "upload":
        uf = st.file_uploader("Drop your resume file here", type=["pdf","docx","txt"], key="imp_file")
        do_ext = st.checkbox("Save as reusable template", value=True, key="imp_do_ext")
        tname  = st.text_input("Template name", "my_style", key="imp_tname")

        if uf and st.button("🚀 Extract & Import", type="primary", key="imp_go", use_container_width=True):
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
            st.markdown(f"**`{b['header']}`**")
            sc = st.selectbox("Category",list(CATS),format_func=lambda x:CATS[x],
                              index=di,key=f"wz_{i}")
            st.text_area("Preview","\n".join(b["lines"][:3]),
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
                save_to_disk(parsed)
                st.session_state.last_hash = ""
                st.session_state.wiz_step = "upload"
                st.session_state.wiz_blk  = []
                st.session_state.wiz_lay  = None
                st.session_state.show_import = False
                st.rerun()

if st.session_state.get("show_import", False):
    st.session_state.show_import = False
    show_import_dialog()







# ═══════════════════════════════════════════════════════
# ③ TWO-PANEL LAYOUT OR CAREER CENTER
# ═══════════════════════════════════════════════════════
def get_profile_metrics(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        personal = data.get("personal", {})
        name = personal.get("name", "SEJAL BHAGAT")
        email = personal.get("email", "")
        exp_count = len(data.get("experience", []))
        proj_count = len(data.get("projects", []))
        skills = data.get("technical_skills", {})
        skills_count = sum(len(v.split(",")) for v in skills.values()) if isinstance(skills, dict) else 0
        return {
            "name": name,
            "email": email,
            "exp_count": exp_count,
            "proj_count": proj_count,
            "skills_count": skills_count
        }
    except Exception:
        return {
            "name": "SEJAL BHAGAT",
            "email": "",
            "exp_count": 0,
            "proj_count": 0,
            "skills_count": 0
        }

def format_relative_time(timestamp: float) -> str:
    diff = time.time() - timestamp
    if diff < 60:
        return "Just now"
    elif diff < 3600:
        mins = int(diff / 60)
        return f"{mins} minute{'s' if mins > 1 else ''} ago"
    elif diff < 86400:
        hours = int(diff / 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff < 172800:
        return "Yesterday"
    else:
        days = int(diff / 86400)
        if days < 7:
            return f"{days} day{'s' if days > 1 else ''} ago"
        else:
            struct = time.localtime(timestamp)
            return time.strftime("%d %b %Y", struct)

@st.dialog("Create New Resume")
def show_create_resume_dialog():
    new_title = st.text_input("Resume Title", placeholder="e.g. Full Stack Developer Resume")
    
    st.markdown("**Select Template Theme**")
    tpl_options = list(ALL_TEMPLATES.keys())
    tpl_names = {k: v["name"] for k, v in ALL_TEMPLATES.items()}
    
    sel_tpl = st.selectbox("Template", options=tpl_options, format_func=lambda k: tpl_names[k], label_visibility="collapsed")
    
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("Cancel", use_container_width=True):
            st.rerun()
    with c_btn2:
        if st.button("Create Resume", type="primary", use_container_width=True):
            if new_title.strip():
                clean_title = re.sub(r"[^a-zA-Z0-9\s_-]", "", new_title).strip()
                file_base = clean_title.lower().replace(" ", "_")
                new_path = os.path.join(PROJECT_ROOT, "resume_versions", f"{file_base}.json")
                counter = 1
                while os.path.exists(new_path):
                    new_path = os.path.join(PROJECT_ROOT, "resume_versions", f"{file_base}_{counter}.json")
                    counter += 1
                
                content = copy.deepcopy(DEFAULT)
                content["metadata"] = {
                    "title": clean_title,
                    "template": sel_tpl,
                    "color": ACCENT_PRESETS["Indigo"],
                    "margins": 20,
                    "fscale": 1.0,
                    "fitting": FITTING_OPTS[0],
                    "last_edited": time.time()
                }
                with open(new_path, "w", encoding="utf-8") as f:
                    json.dump(content, f, indent=2)
                
                load_active_resume(new_path)
                st.session_state.navigation_page = "workspace"
                st.session_state.editor_step = 0
                st.rerun()

def show_home():
    """Phase 1: My Resumes Dashboard containing Recent Resumes card grid."""
    st.markdown("""
    <style>
    .resume-card-container {
      background: #FFFFFF;
      border: 1px solid #E2E8F0;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
      transition: all 0.2s ease;
      margin-bottom: 20px;
    }
    .resume-card-container:hover {
      box-shadow: 0 10px 15px -3px rgba(0,0,0,0.08);
      transform: translateY(-2px);
      border-color: #A5B4FC;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header Row
    st.markdown(
        '<div style="margin: 20px 0 16px;">'
        '<h1 style="font-size: 2.2rem; font-weight: 800; color: #1E293B; margin: 0; letter-spacing: -0.03em;">My Resumes</h1>'
        '<p style="color: #64748B; font-size: 0.95rem; margin: 6px 0 0;">Create, duplicate, and design your resume documents.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    resumes = list_resumes()
    
    # Grid construction: 3 columns
    cols = st.columns(3, gap="medium")
    
    # 1. First card: Create New Resume
    with cols[0]:
        st.markdown(
            '<div class="resume-card-container" style="border: 2px dashed #CBD5E1; background: #F8FAFC; text-align: center; height: 215px; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px;">'
            '<div style="font-size: 2.5rem; color: #94A3B8; margin-bottom: 10px;">➕</div>'
            '<div style="font-weight: 700; color: #475569; font-size: 1.1rem; margin-bottom: 4px;">Create New Resume</div>'
            '<div style="font-size: 0.82rem; color: #94A3B8;">Start from a fresh template</div>'
            '</div>',
            unsafe_allow_html=True
        )
        if st.button("✨ Create New", key="btn_create_new_dashboard", use_container_width=True, type="primary"):
            show_create_resume_dialog()

    # 2. Iterate through existing resumes
    for idx, r in enumerate(resumes):
        col = cols[(idx + 1) % 3]
        with col:
            # Color name mapping
            color_hex = r["color"]
            accent_name = next((name for name, hex_val in ACCENT_PRESETS.items() if hex_val == color_hex), "Indigo")
            tpl_disp = ALL_TEMPLATES.get(r["template"], {}).get("name", r["template"])
            rel_time = format_relative_time(r["last_edited"])
            
            # CSS Thumbnail preview card
            st.markdown(
                f'<div class="resume-card-container">'
                f'<div style="background: {color_hex}15; border-bottom: 1px solid #F1F5F9; height: 110px; display: flex; align-items: center; justify-content: center; position: relative;">'
                f'  <div style="background: white; width: 62px; height: 85px; border-radius: 4px; box-shadow: 0 4px 10px rgba(0,0,0,0.06); padding: 8px; display: flex; flex-direction: column; gap: 3.5px; border: 1px solid #E2E8F0;">'
                f'    <div style="height: 5px; width: 18px; background: {color_hex}; border-radius: 1px;"></div>'
                f'    <div style="height: 2px; width: 35px; background: #E2E8F0; border-radius: 0.5px;"></div>'
                f'    <div style="height: 2px; width: 28px; background: #E2E8F0; border-radius: 0.5px; margin-bottom: 2px;"></div>'
                f'    <div style="height: 1.5px; width: 45px; background: #F1F5F9; border-radius: 0.5px;"></div>'
                f'    <div style="height: 1.5px; width: 40px; background: #F1F5F9; border-radius: 0.5px;"></div>'
                f'    <div style="height: 1.5px; width: 42px; background: #F1F5F9; border-radius: 0.5px;"></div>'
                f'  </div>'
                f'  <div style="position: absolute; bottom: 8px; right: 8px; background: rgba(255,255,255,0.92); font-size: 0.65rem; font-weight: 700; color: #475569; padding: 2px 7px; border-radius: 100px; border: 0.5px solid #E2E8F0;">'
                f'    {tpl_disp}'
                f'  </div>'
                f'</div>'
                f'<div style="padding: 12px 14px 10px;">'
                f'  <div style="font-weight: 700; font-size: 0.95rem; color: #1E293B; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{r["title"]}</div>'
                f'  <div style="font-size: 0.76rem; color: #64748B; margin-top: 2px;">Edited {rel_time}</div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )
            
            # Action Row
            c_open, c_act = st.columns([3.5, 1.5])
            with c_open:
                if st.button("✏️ Edit", key=f"btn_edit_res_{idx}", use_container_width=True, type="primary"):
                    load_active_resume(r["path"])
                    st.session_state.navigation_page = "workspace"
                    st.session_state.editor_step = 0
                    st.rerun()
            with c_act:
                with st.popover("⚙️", use_container_width=True, help="Manage resume"):
                    st.markdown("**Manage Resume**")
                    
                    # Rename Input
                    new_title = st.text_input("Rename", value=r["title"], key=f"ren_input_{idx}")
                    if st.button("Rename", key=f"ren_confirm_{idx}", use_container_width=True):
                        if new_title.strip() and new_title.strip() != r["title"]:
                            with open(r["path"], "r", encoding="utf-8") as f:
                                data = json.load(f)
                            if "metadata" not in data:
                                data["metadata"] = {}
                            data["metadata"]["title"] = new_title.strip()
                            with open(r["path"], "w", encoding="utf-8") as f:
                                json.dump(data, f, indent=2)
                            _read_json.clear()
                            st.rerun()
                            
                    # Duplicate Button
                    if st.button("Duplicate", key=f"dup_confirm_{idx}", use_container_width=True):
                        base_name = os.path.splitext(os.path.basename(r["path"]))[0]
                        new_path = os.path.join(PROJECT_ROOT, "resume_versions", f"{base_name}_copy.json")
                        counter = 1
                        while os.path.exists(new_path):
                            new_path = os.path.join(PROJECT_ROOT, "resume_versions", f"{base_name}_copy_{counter}.json")
                            counter += 1
                        with open(r["path"], "r", encoding="utf-8") as f:
                            content = json.load(f)
                        if "metadata" not in content:
                            content["metadata"] = {}
                        content["metadata"]["title"] = f"{r['title']} Copy"
                        content["metadata"]["last_edited"] = time.time()
                        with open(new_path, "w", encoding="utf-8") as f:
                            json.dump(content, f, indent=2)
                        st.rerun()
                        
                    # Delete Button
                    is_root = (os.path.abspath(r["path"]) == os.path.abspath(os.path.join(PROJECT_ROOT, "resume.json")))
                    if st.button("🗑️ Delete", key=f"del_confirm_{idx}", use_container_width=True, disabled=is_root, help="Original default resume cannot be deleted"):
                        if os.path.exists(r["path"]):
                            os.remove(r["path"])
                        st.rerun()



def _step_done(step_idx: int, data: dict) -> bool:
    p = data.get("personal", {})
    if step_idx == 0:
        return bool(p.get("name") and p.get("email"))
    if step_idx == 1:
        return bool(data.get("education"))
    if step_idx == 2:
        return bool(data.get("experience"))
    if step_idx == 3:
        return bool(data.get("projects"))
    if step_idx == 4:
        sk = data.get("technical_skills", {})
        return bool(sk and any(v.strip() for v in sk.values()))
    return False

# ── SUB-HEADER PROGRESS CARD & TAB ROUTING ──
comp_score, comp_status = calculate_completion_status(st.session_state.resume)
current_step = st.session_state.get("editor_step", 0)

WIZARD_STEPS = [
    ("👤", "Personal"),
    ("🎓", "Education"),
    ("💼", "Experience"),
    ("🚀", "Projects"),
    ("🛠️", "Skills"),
    ("✅", "Review"),
]

STEP_SUBTITLES = [
    "Add your basic details. This information appears at the top of your resume.",
    "Add your academic history, achievements, and extracurricular positions.",
    "Detail your professional roles, responsibilities, and achievements.",
    "Showcase your best engineering and development projects.",
    "Group your technical skills, tools, certifications, and achievements.",
    "Review your resume status, configure page layout, and download the PDF."
]

step_title = WIZARD_STEPS[current_step][1]
step_subtitle = STEP_SUBTITLES[current_step]

# Calculate motivational status metrics
done_count = sum(1 for i in range(5) if _step_done(i, st.session_state.resume))
sections_remaining = 5 - done_count
next_section_idx = next((i for i in range(5) if not _step_done(i, st.session_state.resume)), 5)
if next_section_idx < 5:
    next_section_name = WIZARD_STEPS[next_section_idx][1]
else:
    next_section_name = "Review & Finish"

        pname = d.get("personal",{}).get("name","Resume")
        safe  = re.sub(r"[^a-zA-Z0-9]","_",pname).strip("_") or "Resume"
        if st.session_state.cok and st.session_state.pdf_raw:
            dl1, dl2 = st.columns(2)
            with dl1:
                st.download_button("📥 PDF",
                    data=st.session_state.pdf_raw,
                    file_name=f"{safe}_Resume.pdf",
                    mime="application/pdf",
                    use_container_width=True, type="primary", key="wz_dl_pdf")
            with dl2:
                st.download_button("📋 JSON",
                    data=json.dumps(st.session_state.resume, indent=2).encode(),
                    file_name="resume_data.json",
                    mime="application/json",
                    use_container_width=True, key="wz_dl_json")

        with st.expander("⚙️ Advanced Settings — margin, font, fitting", expanded=False):
            st.markdown('<div class="sec-title">Page Layout</div>', unsafe_allow_html=True)
            new_m = st.slider("Margin (pt)", 10, 36, M, 2, key="wz_adv_mg")
            m_txt, m_cls = margin_label(new_m)
            st.markdown(f'Current: <b>{new_m}pt</b> → <span class="setting-effect {m_cls}">{m_txt}</span>', unsafe_allow_html=True)
            new_fs = st.slider("Font Scale", 0.75, 1.25, FS, 0.05, key="wz_adv_fs")
            fs_txt, fs_cls = fscale_label(new_fs)
            st.markdown(f'Current: <b>{new_fs:.2f}×</b> → <span class="setting-effect {fs_cls}">{fs_txt}</span>', unsafe_allow_html=True)
            new_ft = st.radio("Page Fitting", FITTING_OPTS, index=FITTING_OPTS.index(FT),
                              key="wz_adv_fit", label_visibility="collapsed", horizontal=True)
            if (new_m != M) or (new_fs != FS) or (new_ft != FT):
                st.session_state.margins = new_m
                st.session_state.fscale  = new_fs
                st.session_state.fitting = new_ft
                st.session_state.last_hash = ""
                st.rerun()

        with st.expander("🌐 Web Portfolio", expanded=False):
            try:
                from resume_builder.portfolio import exporter as pe
                if st.button("Generate Portfolio HTML", key="wz_port_gen", use_container_width=True):
                    with st.spinner("Generating…"):
                        hc = pe.generate_portfolio_html(d, C)
                        os.makedirs(os.path.join("resume_builder","exports","html"), exist_ok=True)
                        hp = os.path.join("resume_builder","exports","html","index.html")
                        with open(hp,"w",encoding="utf-8") as hf: hf.write(hc)
                        st.download_button("📥 Download index.html", data=hc.encode(),
                                           file_name="index.html", mime="text/html",
                                           use_container_width=True, key="wz_dl_port")
            except Exception as ex:
                st.error(f"Portfolio error: {ex}")

    # ══════════════════════════════════════════════════════════════════════
    # WIZARD NAVIGATION — Back / Next buttons
    st.markdown('<div class="hdiv"></div>', unsafe_allow_html=True)
    btn_l, btn_r = st.columns([1, 1])
    with btn_l:
        prev_disabled = (current_step == 0)
        if st.button("← Previous", key="wz_prev_btn", disabled=prev_disabled, use_container_width=True):
            st.session_state.editor_step = current_step - 1
            st.rerun()
    with btn_r:
        if current_step < len(WIZARD_STEPS) - 1:
            next_label = WIZARD_STEPS[current_step + 1][1]
            if st.button(f"Next: {next_label} →", key="wz_next_btn", use_container_width=True, type="primary"):
                # Save data
                live = collect_resume()
                if live != st.session_state.resume:
                    push_undo(st.session_state.resume)
                    st.session_state.resume = live
                    save_to_disk(live)
                    st.session_state.last_hash = ""
                st.session_state.editor_step = current_step + 1
                st.rerun()
        else:
            if st.button("🏠 Go Home", key="wz_finish_btn", use_container_width=True, type="primary"):
                st.session_state.navigation_page = "home"
                st.rerun()


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
    
    lh_col1, lh_col2 = st.columns([1.8, 1.2])
    with lh_col1:
        st.markdown(
            '<div style="display: flex; align-items: center; gap: 8px; height: 38px;">'
            '<span style="font-weight: 700; font-size: 1.15rem; color: #1E293B;">Live Preview</span>'
            '<span style="font-size: 0.78rem; color: #10B981; font-weight: 600; display: flex; align-items: center; gap: 4px;">'
            '<span style="height: 6px; width: 6px; background-color: #10B981; border-radius: 50%; display: inline-block;"></span>'
            'Auto-updated</span>'
            '</div>',
            unsafe_allow_html=True
        )
    with lh_col2:
        lh_sub1, lh_sub2, lh_sub3 = st.columns([1.6, 0.8, 0.8])
        with lh_sub1:
            zoom_options = ["Fit Width", "100%", "75%"]
            st.selectbox("Zoom", options=zoom_options, key="preview_zoom", label_visibility="collapsed")
        with lh_sub2:
            is_desk = (st.session_state.get("device_view", "desktop") == "desktop")
            if st.button("💻", key="btn_view_desk", type="primary" if is_desk else "secondary", help="Desktop view"):
                st.session_state.device_view = "desktop"
                st.rerun()
        with lh_sub3:
            is_mob = (st.session_state.get("device_view", "desktop") == "mobile")
            if st.button("📱", key="btn_view_mob", type="primary" if is_mob else "secondary", help="Mobile view"):
                st.session_state.device_view = "mobile"
                st.rerun()

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
        # Determine mobile styling
        is_mobile_view = (st.session_state.get("device_view", "desktop") == "mobile")
        mobile_style_css = ".page-wrapper { max-width: 360px !important; margin: 0 auto !important; }" if is_mobile_view else ""
        
        pdf_b64 = st.session_state.pdf_b64
        pdf_js_b64, pdf_worker_b64 = load_local_pdfjs_assets()
        pdf_html = f"""<!DOCTYPE html>
<html>
<head>
<script>
  // Decode and inject PDF.js library inline to avoid cross-origin / tracking blockers
  const pdfJsContent = atob("{pdf_js_b64}");
  const scriptEl = document.createElement('script');
  scriptEl.textContent = pdfJsContent;
  document.head.appendChild(scriptEl);
</script>
<style>
  {mobile_style_css}
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
  
  // Create a Blob URL from decoded worker script to run it locally in a separate thread
  const pdfWorkerContent = atob("{pdf_worker_b64}");
  const blob = new Blob([pdfWorkerContent], {{type: 'application/javascript'}});
  const workerURL = URL.createObjectURL(blob);
  pdfjsLib.GlobalWorkerOptions.workerSrc = workerURL;

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

# ═══════════════════════════════════════════════════════
# ④ FIXED BOTTOM ACTIONS BAR (workspace view only)
# ═══════════════════════════════════════════════════════
if st.session_state.navigation_page == "workspace":
    st.markdown('<div id="bottom-bar-marker"></div>', unsafe_allow_html=True)
    
    # 6 columns for bottom bar
    bf1, bf2, bf3, bf4, bf5, bf6 = st.columns([1, 1.2, 1, 1.2, 0.8, 1.4])
    
    # Calculate health score dynamically
    hs_score = calculate_health_score(d)["score"]
    
    with bf1:
        # Templates toggle dialog/expander could be wired, or we can just show templates options inline in Step 5.
        # Clicking templates here can set editor_step to 5 (Review/Finish) where template settings reside!
        if st.button("🎨 Templates", key="fbar_templates", use_container_width=True):
            st.session_state.editor_step = 5
            st.rerun()
            
    with bf2:
        if st.button(f"📊 {hs_score} Health Score", key="fbar_health", use_container_width=True):
            st.session_state.navigation_page = "career"
            st.session_state.career_active_tool = "health_scorer"
            st.rerun()
            
    with bf3:
        if st.button("🔍 Check ATS", key="fbar_ats", use_container_width=True):
            st.session_state.navigation_page = "career"
            st.session_state.career_active_tool = "consistency"
            st.rerun()
            
    with bf4:
        if st.button("📥 Import Resume", key="fbar_import", use_container_width=True):
            st.session_state.show_import = True
            st.rerun()
            
    with bf5:
        if st.button("💾 Save", key="fbar_save", use_container_width=True):
            live = collect_resume()
            push_undo(st.session_state.resume)
            st.session_state.resume = live
            save_to_disk(live)
            st.session_state.last_hash = ""
            st.success("✅ Saved!")
            st.rerun()
            
    with bf6:
        pname = d.get("personal",{}).get("name","Resume")
        safe_name = re.sub(r"[^a-zA-Z0-9]","_",pname).strip("_") or "Resume"
        if st.session_state.pdf_raw:
            st.download_button(
                "📥 Download PDF",
                data=st.session_state.pdf_raw,
                file_name=f"{safe_name}_Resume.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary",
                key="fbar_dl_pdf"
            )
        else:
            st.button("📥 Download PDF", key="fbar_dl_pdf_disabled", disabled=True, use_container_width=True)

