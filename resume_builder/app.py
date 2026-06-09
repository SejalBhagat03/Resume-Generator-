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
from resume_builder.utils.achievement_quantifier import AchievementQuantifier
from resume_builder.utils.gap_analyzer import CareerGapAnalyzer
from resume_builder.utils.github_integration import GitHubIntegration

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

.repo-card {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 18px;
  padding: 18px;
  box-shadow: 0 10px 30px rgba(15,23,42,0.04);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.repo-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 16px 40px rgba(15,23,42,0.08);
}
.repo-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 14px;
}
.repo-card-title {
  font-size: 1rem;
  font-weight: 700;
  color: #111827;
  margin-bottom: 8px;
}
.repo-card-description {
  color: #475569;
  font-size: 0.92rem;
  line-height: 1.5;
  margin-bottom: 14px;
  min-height: 62px;
}
.repo-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 12px;
  margin-bottom: 14px;
}
.repo-chip {
  background: #EEF2FF;
  color: #312E81;
  border-radius: 999px;
  font-size: 0.75rem;
  padding: 6px 10px;
  font-weight: 600;
}
.repo-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 16px;
}
.repo-stat {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.82rem;
  color: #475569;
}
.repo-score-badge {
  background: #E0E7FF;
  color: #3730A3;
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 0.78rem;
  font-weight: 700;
}
.repo-card a {
  color: #4338CA;
  text-decoration: none;
}
.repo-card a:hover {
  text-decoration: underline;
}

.github-filter-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}
.github-filter-row > div {
  min-width: 180px;
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

/* ── Mobile Responsiveness (Viewport width <= 768px) ── */
@media (max-width: 768px) {
  /* Reduce page container padding on mobile to maximize space */
  .block-container {
    padding: 1rem 1rem !important;
  }

  /* 1. Header Navigation Columns Wrapping */
  div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] {
    flex-direction: row !important;
    flex-wrap: wrap !important;
    gap: 8px 6px !important;
    padding: 10px !important;
  }
  div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] > [data-testid="column"] {
    min-width: 0 !important;
    max-width: none !important;
    width: auto !important;
    flex-grow: 1 !important;
    flex-shrink: 1 !important;
    flex-basis: auto !important;
  }
  /* Reorder and sizing on mobile */
  div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(1) { /* Back button */
    order: 1 !important; flex-basis: 22% !important;
  }
  div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2) { /* Title */
    order: 2 !important; flex-basis: 48% !important;
  }
  div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(3) { /* Saved */
    order: 3 !important; flex-basis: 24% !important;
  }
  div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(5) { /* Edit button */
    order: 4 !important; flex-basis: 31% !important;
  }
  div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(6) { /* Preview button */
    order: 5 !important; flex-basis: 31% !important;
  }
  div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(7) { /* Insights button */
    order: 6 !important; flex-basis: 31% !important;
  }
  div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(4) { /* History popover */
    order: 7 !important; flex-basis: 47% !important;
  }
  div:has(#top-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(8) { /* Accent color select */
    order: 8 !important; flex-basis: 47% !important;
  }

  /* 2. Stepper Widget Wrapping */
  div:has(#sub-header-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] {
    flex-direction: row !important;
    flex-wrap: wrap !important;
    padding: 8px !important;
    gap: 6px !important;
  }
  div:has(#sub-header-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] > [data-testid="column"] {
    width: auto !important;
    min-width: 0 !important;
    flex-grow: 1 !important;
    flex-basis: auto !important;
  }
  div:has(#sub-header-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(1) { /* Metadata info */
    flex-basis: 100% !important;
    margin-bottom: 4px !important;
  }
  div:has(#sub-header-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(n+2) { /* Step buttons */
    flex-basis: 14% !important;
  }
  div:has(#sub-header-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"]::before {
    display: none !important; /* Hide connector line */
  }
  .step-label {
    font-size: 0.6rem !important;
    text-overflow: ellipsis !important;
    overflow: hidden !important;
    white-space: nowrap !important;
  }

  /* 3. Fixed Bottom Actions Bar */
  div:has(#bottom-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] {
    padding: 8px 12px !important;
    gap: 8px !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
  }
  div:has(#bottom-bar-marker) + div[data-testid="element-container"] > [data-testid="stHorizontalBlock"] > [data-testid="column"] {
    width: 50% !important;
    min-width: 0 !important;
    flex: 1 1 50% !important;
  }

  /* 4. Hide sticky preview panel on mobile during Edit view */
  div[data-testid="column"]:has(#right-panel-anchor) {
    display: none !important;
  }
  
  /* 5. Continue Last Resume Banner Stack */
  div[data-testid="stHorizontalBlock"]:has(#btn_continue_latest) {
    flex-direction: column !important;
    gap: 12px !important;
  }
  div[data-testid="stHorizontalBlock"]:has(#btn_continue_latest) > div[data-testid="column"] {
    width: 100% !important;
    flex: 1 1 100% !important;
  }
  .continue-banner-box {
    height: auto !important;
    min-height: 95px !important;
    padding: 12px 16px !important;
  }
}

/* ── Resume Card: style Streamlit's native bordered container ── */
div[data-testid="stVerticalBlockBorderWrapper"] {
  background: #FFFFFF !important;
  border-radius: 16px !important;
  border: 1px solid #E2E8F0 !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
  transition: box-shadow 0.18s ease, transform 0.18s ease, border-color 0.18s ease !important;
  overflow: hidden !important;
  margin-bottom: 6px !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
  box-shadow: 0 10px 24px rgba(99,102,241,0.13) !important;
  transform: translateY(-3px) !important;
  border-color: #6366F1 !important;
}

/* On mobile, stack cards single-column */
@media (max-width: 768px) {
  div[data-testid="stHorizontalBlock"]:has(div[data-testid="stVerticalBlockBorderWrapper"]) {
    flex-direction: column !important;
    gap: 0 !important;
  }
  div[data-testid="stHorizontalBlock"]:has(div[data-testid="stVerticalBlockBorderWrapper"]) > div[data-testid="column"] {
    width: 100% !important;
    flex: 1 1 100% !important;
    min-width: 0 !important;
    max-width: none !important;
  }
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
_s("navigation_page", "home")
_s("editor_step", 0)
_s("workspace_tab", "Edit")
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

    # Compile PDF on save so the thumbnail is always up to date
    try:
        pdf_path = get_profile_path().replace(".json", ".pdf")
        build_pdf(
            data=d,
            template_id=meta["template"],
            pdf_filename=pdf_path,
            accent_color=meta["color"],
            font_scale=meta["fscale"],
            margin_size=meta["margins"],
            auto_compress=(meta["fitting"] == FITTING_OPTS[0]),
            allow_multi_page=(meta["fitting"] == FITTING_OPTS[2]),
        )
    except Exception:
        pass


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

def get_pdf_base64_for_resume(r) -> str:
    path = r["path"]
    pdf_path = path.replace(".json", ".pdf")
    if not os.path.exists(pdf_path):
        try:
            from resume_builder.generators.pdf_generator import build_pdf
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            build_pdf(
                data=data,
                template_id=r.get("template", "sejal_original"),
                pdf_filename=pdf_path,
                accent_color=r.get("color", "#6366F1"),
            )
        except Exception:
            pass
    if os.path.exists(pdf_path):
        try:
            with open(pdf_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            pass
    return ""

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


def save_checkpoint(path: str, data: dict):
    """Save a resume version snapshot to the history directory."""
    if not path or not os.path.exists(path):
        return
    base_name = os.path.splitext(os.path.basename(path))[0]
    history_dir = os.path.join(PROJECT_ROOT, "resume_versions", "history", base_name)
    os.makedirs(history_dir, exist_ok=True)
    
    # List existing checkpoints
    checkpoint_files = [f for f in os.listdir(history_dir) if f.endswith(".json")]
    if checkpoint_files:
        checkpoint_files.sort(key=lambda x: os.path.getmtime(os.path.join(history_dir, x)), reverse=True)
        latest_cp_path = os.path.join(history_dir, checkpoint_files[0])
        try:
            with open(latest_cp_path, "r", encoding="utf-8") as f:
                latest_data = json.load(f)
            # Remove metadata timestamps for comparison
            d1 = copy.deepcopy(data)
            d2 = copy.deepcopy(latest_data)
            if "metadata" in d1: d1["metadata"].pop("last_edited", None)
            if "metadata" in d2: d2["metadata"].pop("last_edited", None)
            if d1 == d2:
                return # identical
        except Exception:
            pass
            
    version_num = len(checkpoint_files) + 1
    timestamp = int(time.time())
    cp_filename = f"version_{version_num}_{timestamp}.json"
    cp_path = os.path.join(history_dir, cp_filename)
    try:
        with open(cp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


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
    personal = {
        "name":     g("f_nm",  d.get("personal",{}).get("name","")),
        "title":    g("f_title", d.get("personal",{}).get("title","")),
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
        "portfolio": {
            "display": g("f_portd", d.get("personal",{}).get("portfolio",{}).get("display","")),
            "url":     g("f_portu", d.get("personal",{}).get("portfolio",{}).get("url","")),
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

    return {
        "metadata": d.get("metadata", {}),
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


# ═══════════════════════════════════════════════════════
# ① TOP BAR / EDITOR HEADER
# ═══════════════════════════════════════════════════════
st.markdown('<div id="top-bar-marker"></div>', unsafe_allow_html=True)

page = st.session_state.navigation_page

if page == "workspace":
    # Set default workspace tab
    if "workspace_tab" not in st.session_state:
        st.session_state.workspace_tab = "Edit"
        
    c_back, c_title, c_saved, c_history, c_edit, c_prev, c_ins, c_accent = st.columns(
        [1.2, 2.5, 0.8, 1.2, 0.8, 0.8, 0.9, 1.0], gap="small"
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
        st.markdown('<div style="display: flex; align-items: center; justify-content: center; height: 38px;"><span style="color: #10B981; font-weight: 700; font-size: 0.85rem;">✓ Saved</span></div>', unsafe_allow_html=True)
        
    with c_history:
        base_name = os.path.splitext(os.path.basename(get_profile_path()))[0]
        history_dir = os.path.join(PROJECT_ROOT, "resume_versions", "history", base_name)
        checkpoints = []
        if os.path.exists(history_dir):
            for f in os.listdir(history_dir):
                if f.endswith(".json"):
                    fpath = os.path.join(history_dir, f)
                    mtime = os.path.getmtime(fpath)
                    checkpoints.append({
                        "filename": f,
                        "path": fpath,
                        "time": mtime
                    })
            checkpoints.sort(key=lambda x: x["time"], reverse=True)
            
        with st.popover("📜 History", use_container_width=True, help="View and restore checkpoints"):
            st.markdown("**Version Checkpoints**")
            if not checkpoints:
                st.caption("No snapshots saved yet.")
            else:
                for cp in checkpoints[:10]:
                    cp_parts = cp["filename"].replace(".json", "").split("_")
                    cp_name = f"Version {cp_parts[1]}"
                    rel_time = format_relative_time(cp["time"])
                    cp_col1, cp_col2 = st.columns([6.8, 3.2])
                    with cp_col1:
                        st.markdown(f"**{cp_name}** ({rel_time})")
                    with cp_col2:
                        if st.button("Restore", key=f"restore_cp_{cp['filename']}"):
                            with open(cp["path"], "r", encoding="utf-8") as f:
                                restored_data = json.load(f)
                            push_undo(st.session_state.resume)
                            st.session_state.resume = restored_data
                            save_to_disk(restored_data)
                            st.success(f"Restored {cp_name}!")
                            st.rerun()
            if st.button("📸 Save Checkpoint", key="btn_save_cp_manual", use_container_width=True):
                save_checkpoint(get_profile_path(), st.session_state.resume)
                st.success("Checkpoint saved!")
                st.rerun()
        
    with c_edit:
        is_active_edit = (st.session_state.workspace_tab == "Edit")
        if st.button("✏️ Edit", key="btn_wtab_edit", type="primary" if is_active_edit else "secondary", use_container_width=True):
            st.session_state.workspace_tab = "Edit"
            st.session_state.navigation_page = "workspace"
            st.rerun()
            
    with c_prev:
        is_active_prev = (st.session_state.workspace_tab == "Preview")
        if st.button("👁️ Preview", key="btn_wtab_prev", type="primary" if is_active_prev else "secondary", use_container_width=True):
            st.session_state.workspace_tab = "Preview"
            st.session_state.navigation_page = "workspace"
            st.rerun()
            
    with c_ins:
        is_active_ins = (st.session_state.workspace_tab == "Insights")
        if st.button("📊 Insights", key="btn_wtab_ins", type="primary" if is_active_ins else "secondary", use_container_width=True):
            st.session_state.workspace_tab = "Insights"
            st.session_state.navigation_page = "workspace"
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

def render_pdf_thumbnail(pdf_b64: str, key: str):
    if not pdf_b64:
        st.markdown(
            '<div style="background: #FAFBFF; border-bottom: 1px solid #F1F5F9; height: 110px; display: flex; align-items: center; justify-content: center;">'
            '<span style="font-size: 2rem; color: #CBD5E1;">📄</span>'
            '</div>',
            unsafe_allow_html=True
        )
        return
        
    pdf_js_b64, pdf_worker_b64 = load_local_pdfjs_assets()
    html_content = f"""<!DOCTYPE html>
    <html>
    <head>
    <script>
      const pdfJsContent = atob("{pdf_js_b64}");
      const scriptEl = document.createElement(\'script\');
      scriptEl.textContent = pdfJsContent;
      document.head.appendChild(scriptEl);
    </script>
    <style>
      * {{ box-sizing: border-box; margin: 0; padding: 0; }}
      body, html {{
        background: #F8FAFC;
        overflow: hidden;
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
      }}
      #canvas-container {{
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #F8FAFC;
        padding: 5px;
      }}
      canvas {{
        max-width: 100%;
        max-height: 100%;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border: 1px solid #E2E8F0;
        border-radius: 4px;
        background: #fff;
      }}
    </style>
    </head>
    <body>
    <div id="canvas-container">
      <canvas id="thumbnail-canvas"></canvas>
    </div>
    <script>
      const pdfjsLib = window['pdfjs-dist/build/pdf'];
      
      const pdfWorkerContent = atob("{pdf_worker_b64}");
      const blob = new Blob([pdfWorkerContent], {{type: \'application/javascript\'}});
      const workerURL = URL.createObjectURL(blob);
      pdfjsLib.GlobalWorkerOptions.workerSrc = workerURL;
    
      const base64PDF = "{pdf_b64}";
    
      function b64ToArr(b64) {{
        const raw = atob(b64);
        const arr = new Uint8Array(raw.length);
        for (let i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
        return arr;
      }}
    
      pdfjsLib.getDocument({{ data: b64ToArr(base64PDF) }}).promise.then(async (pdf) => {{
        const page = await pdf.getPage(1);
        const canvas = document.getElementById(\'thumbnail-canvas\');
        const ctx = canvas.getContext(\'2d\');
        
        const viewport = page.getViewport({{ scale: 1.0 }});
        const scale = Math.min(100 / viewport.height, 75 / viewport.width);
        const scaledViewport = page.getViewport({{ scale: scale * 2 }}); 
        
        canvas.height = scaledViewport.height;
        canvas.width = scaledViewport.width;
        canvas.style.height = (scaledViewport.height / 2) + \'px\';
        canvas.style.width = (scaledViewport.width / 2) + \'px\';
        
        await page.render({{ canvasContext: ctx, viewport: scaledViewport }}).promise;
      }}).catch(err => {{
        console.error(\'Thumbnail render error:\', err);
      }});
    </script>
    </body>
    </html>"""
    
    import streamlit.components.v1 as components
    components.html(html_content, height=110, scrolling=False)


@st.dialog("Create New Resume", width="large")
def show_create_resume_dialog():
    # Reset to step 1 when dialog is freshly opened
    if st.session_state.get("wizard_just_opened", True):
        st.session_state.create_wizard_step = 1
        st.session_state.wizard_resume_type = "Fresh Graduate"
        st.session_state.wizard_import_source = "Start Empty"
        st.session_state.wizard_github_username = ""
        st.session_state.wizard_github_repos = []
        st.session_state.wizard_selected_repos = []
        st.session_state.wizard_resume_title = ""
        st.session_state.wizard_template = "sejal_original"
        st.session_state.wizard_just_opened = False

    # Step progress indicator at the top
    step = st.session_state.create_wizard_step
    st.markdown(
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; background: #EEF2FF; padding: 10px 15px; border-radius: 8px; border: 1px solid #C7D2FE;">'
        f'  <span style="font-weight: 700; color: {"#6366F1" if step==1 else "#64748B"};">Step 1: Profile Type</span>'
        f'  <span style="color: #CBD5E1;">&rarr;</span>'
        f'  <span style="font-weight: 700; color: {"#6366F1" if step==2 else "#64748B"};">Step 2: Source / Import</span>'
        f'  <span style="color: #CBD5E1;">&rarr;</span>'
        f'  <span style="font-weight: 700; color: {"#6366F1" if step==3 else "#64748B"};">Step 3: Theme & Finish</span>'
        f'</div>',
        unsafe_allow_html=True
    )

    if step == 1:
        st.markdown("### 👤 Step 1: What are you creating?")
        res_type = st.radio(
            "Select your profile type:",
            options=["Fresh Graduate", "Experienced Professional", "Internship Resume", "Academic Resume", "Custom"],
            key="wizard_res_type_radio"
        )
        st.session_state.wizard_resume_type = res_type
        
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        if st.button("Next ➡️", type="primary", use_container_width=True, key="wiz_next_1"):
            st.session_state.create_wizard_step = 2

    elif step == 2:
        st.markdown("### 📥 Step 2: Choose your starting point")
        imp_source = st.radio(
            "Import details or start from scratch:",
            options=["Start Empty", "Existing Resume", "LinkedIn PDF", "GitHub"],
            key="wizard_imp_source_radio"
        )
        st.session_state.wizard_import_source = imp_source
        
        if imp_source == "GitHub":
            st.markdown("**Enter GitHub Username to fetch projects:**")
            gh_user = st.text_input("GitHub Username", value=st.session_state.get("wizard_github_username", ""), placeholder="e.g. SejalBhagat03")
            if gh_user.strip():
                st.session_state.wizard_github_username = gh_user.strip()
                if st.button("🔍 Fetch Projects", type="primary", use_container_width=True):
                    with st.spinner("Fetching repositories..."):
                        from resume_builder.utils.github_integration import GitHubIntegration
                        repos = GitHubIntegration.fetch_repos(gh_user.strip())
                        st.session_state.wizard_github_repos = repos
                
                repos = st.session_state.get("wizard_github_repos", [])
                if repos:
                    st.markdown("**Select repositories to import as Projects:**")
                    repo_options = [r["name"] for r in repos]
                    selected_repos = st.multiselect("Select projects:", options=repo_options, default=repo_options[:3])
                    st.session_state.wizard_selected_repos = selected_repos
                elif "wizard_github_repos" in st.session_state:
                    st.warning("No public repositories found for this username.")
                    
        elif imp_source in ("Existing Resume", "LinkedIn PDF"):
            st.markdown("**Upload your resume file (PDF, DOCX, TXT):**")
            uploaded_file = st.file_uploader("Upload resume file:", type=["pdf", "docx", "txt"], key="wizard_upload")
            if uploaded_file:
                st.session_state.wizard_uploaded_file = uploaded_file
                
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        w2_col1, w2_col2 = st.columns(2)
        with w2_col1:
            if st.button("⬅️ Back", use_container_width=True, key="wiz_back_2"):
                st.session_state.create_wizard_step = 1
        with w2_col2:
            if st.button("Next ➡️", type="primary", use_container_width=True, key="wiz_next_2"):
                st.session_state.create_wizard_step = 3

    elif step == 3:
        st.markdown("### 🎨 Step 3: Choose template and title")
        
        res_title = st.text_input("Resume Title", value=st.session_state.get("wizard_resume_title", ""), placeholder="e.g. Frontend Developer Resume")
        
        st.markdown("**Select Template Theme**")
        tpl_options = list(ALL_TEMPLATES.keys())
        tpl_names = {k: v["name"] for k, v in ALL_TEMPLATES.items()}
        
        sel_tpl = st.selectbox("Template Theme", options=tpl_options, format_func=lambda k: tpl_names[k])
        st.session_state.wizard_template = sel_tpl
        
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        w3_col1, w3_col2 = st.columns(2)
        with w3_col1:
            if st.button("⬅️ Back", use_container_width=True, key="wiz_back_3"):
                st.session_state.create_wizard_step = 2
        with w3_col2:
            if st.button("🚀 Create Resume", type="primary", use_container_width=True):
                title = res_title.strip() or f"{st.session_state.wizard_resume_type} Resume"
                clean_title = re.sub(r"[^a-zA-Z0-9\s_-]", "", title).strip()
                file_base = clean_title.lower().replace(" ", "_")
                new_path = os.path.join(PROJECT_ROOT, "resume_versions", f"{file_base}.json")
                counter = 1
                while os.path.exists(new_path):
                    new_path = os.path.join(PROJECT_ROOT, "resume_versions", f"{file_base}_{counter}.json")
                    counter += 1
                    
                content = copy.deepcopy(DEFAULT)
                
                # Apply custom summaries based on Wizard Profile Selection
                if st.session_state.wizard_resume_type == "Fresh Graduate":
                    content["summary"] = "Motivated graduate looking to apply engineering principles in a growth-oriented role."
                elif st.session_state.wizard_resume_type == "Experienced Professional":
                    content["summary"] = "Seasoned software development professional with a proven track record of engineering scalable platforms."
                elif st.session_state.wizard_resume_type == "Internship Resume":
                    content["summary"] = "Ambitious student seeking a hands-on developer internship role to build engineering solutions."
                elif st.session_state.wizard_resume_type == "Academic Resume":
                    content["summary"] = "Academic researcher focusing on software systems engineering, algorithms development, and modular design."
                
                # GitHub Import integration
                if st.session_state.wizard_import_source == "GitHub" and st.session_state.wizard_selected_repos:
                    from resume_builder.utils.github_integration import GitHubIntegration
                    gh_analysis = GitHubIntegration.analyze_profile(st.session_state.wizard_github_username)
                    imported_projects = []
                    for rp in gh_analysis.get("suggested_projects", []):
                        if rp["name"] in st.session_state.wizard_selected_repos or rp["name"].replace(" ", "-").lower() in st.session_state.wizard_selected_repos:
                            bullets = [
                                f"Designed and delivered '{rp['name']}' project repository using {rp['tech'] or 'open-source tech'} with complete configurations.",
                                f"Engineered clean modular source logic based on '{rp['description']}' specifications and API models.",
                                f"Configured optimal repository components resulting in an overall high impact score rating of {rp['impact_score']}%."
                            ]
                            imported_projects.append({
                                "title": rp["name"],
                                "link": rp["url"],
                                "date": "2026",
                                "tools": rp["tech"] or "",
                                "bullets": bullets
                            })
                    content["projects"] = imported_projects
                    
                # PDF / Docx extraction import integration
                elif st.session_state.wizard_import_source in ("Existing Resume", "LinkedIn PDF") and st.session_state.get("wizard_uploaded_file"):
                    uf = st.session_state.wizard_uploaded_file
                    tdir = os.path.join("resume_builder","data","temp")
                    os.makedirs(tdir, exist_ok=True)
                    tp = os.path.join(tdir, uf.name)
                    with open(tp,"wb") as tf: tf.write(uf.getbuffer())
                    ext = uf.name.rsplit(".",1)[-1].lower()
                    txt = ""
                    try:
                        if ext == "txt":
                            txt = extract_txt_text(tp)
                        elif ext == "pdf":
                            txt, runs = extract_pdf_layout_and_text(tp)
                        elif ext == "docx":
                            txt, dd = extract_docx_layout_and_text(tp)
                    except Exception as ex:
                        st.error(f"Extraction error: {ex}")
                    finally:
                        try: os.remove(tp)
                        except: pass
                    if txt:
                        blocks = segment_into_blocks(txt)
                        mapped = []
                        for b in blocks:
                            mapped.append({"header": b["header"], "category": b.get("inferred_category", "ignore"), "lines": b["lines"]})
                        parsed = parse_mapped_blocks_to_json(mapped)
                        content.update(parsed)
                
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
                    
                st.session_state.create_wizard_step = 1
                st.session_state.wizard_just_opened = True  # Reset for next open
                if "wizard_uploaded_file" in st.session_state:
                    del st.session_state.wizard_uploaded_file
                if "wizard_github_repos" in st.session_state:
                    del st.session_state.wizard_github_repos
                    
                load_active_resume(new_path)
                st.session_state.navigation_page = "workspace"
                st.session_state.editor_step = 0
                st.rerun()

def show_home():
    """Phase 1: My Resumes Dashboard containing Recent Resumes card grid."""
    # Card hover effect is handled in global CSS for [data-testid="stVerticalBlockBorderWrapper"]

    # Header Row
    st.markdown(
        '<div style="margin: 20px 0 16px;">'
        '<h1 style="font-size: 2.2rem; font-weight: 800; color: #1E293B; margin: 0; letter-spacing: -0.03em;">My Resumes</h1>'
        '<p style="color: #64748B; font-size: 0.95rem; margin: 6px 0 0;">Create, duplicate, and design your resume documents.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    resumes = list_resumes()

    # Continue Last Resume Banner
    if resumes:
        latest = resumes[0]
        rel_time = format_relative_time(latest["last_edited"])
        b_col1, b_col2 = st.columns([7.5, 2.5])
        with b_col1:
            st.markdown(
                f'<div class="continue-banner-box" style="background: linear-gradient(135deg, #EEF2FF 0%, #F5F3FF 100%); '
                f'border: 1px solid #C7D2FE; border-left: 5px solid #6366F1; border-radius: 12px; '
                f'padding: 16px 20px; height: 95px; display: flex; flex-direction: column; justify-content: center; line-height: 1.35;">'
                f'  <span style="font-size: 0.72rem; font-weight: 700; color: #6366F1; text-transform: uppercase; letter-spacing: 0.08em;">Continue Editing</span>'
                f'  <span style="font-size: 1.15rem; font-weight: 800; color: #1E293B; margin-top: 3px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{latest["title"]}</span>'
                f'  <span style="font-size: 0.8rem; color: #64748B; margin-top: 2px;">Last edited {rel_time} &middot; Theme: {latest["template"].replace("_", " ").title()}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
        with b_col2:
            st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)
            if st.button("⚡ Continue", key="btn_continue_latest", use_container_width=True, type="primary", help="Continue editing your most recent resume"):
                load_active_resume(latest["path"])
                st.session_state.navigation_page = "workspace"
                st.session_state.editor_step = 0
                st.rerun()
        st.markdown('<div style="height: 15px;"></div>', unsafe_allow_html=True)

    # Quick Search Box
    search_query = st.text_input("🔍 Search Resume", placeholder="Search by resume title or template...", key="home_search_input", label_visibility="collapsed")
    if search_query:
        search_query_clean = search_query.strip().lower()
        resumes = [r for r in resumes if search_query_clean in r["title"].lower() or search_query_clean in r["template"].lower()]

    st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)

    # Grid construction: chunk resumes into rows of 3 (ensures chronological order on mobile)
    # List of all cards to render
    cards = [{"type": "create_new"}] + [{"type": "resume", "data": r, "res_idx": i} for i, r in enumerate(resumes)]
    
    # Render cards in rows of 3 columns
    for i in range(0, len(cards), 3):
        chunk = cards[i:i+3]
        cols = st.columns(3, gap="medium")
        for idx_c, card in enumerate(chunk):
            with cols[idx_c]:
                if card["type"] == "create_new":
                    with st.container(border=True):
                        st.markdown(
                            '<div style="text-align: center; padding: 24px 8px 16px;">'
                            '<div style="font-size: 2.8rem; color: #A5B4FC; margin-bottom: 10px;">➕</div>'
                            '<div style="font-weight: 700; color: #475569; font-size: 1.05rem; margin-bottom: 4px;">Create New Resume</div>'
                            '<div style="font-size: 0.82rem; color: #94A3B8;">Start from a fresh template</div>'
                            '</div>',
                            unsafe_allow_html=True
                        )
                        if st.button("✨ Create New", key="btn_create_new_dashboard", use_container_width=True, type="primary"):
                            st.session_state.wizard_just_opened = True
                            show_create_resume_dialog()
                else:
                    # Existing resume card rendering
                    r = card["data"]
                    idx = card["res_idx"]
                    
                    tpl_disp = ALL_TEMPLATES.get(r["template"], {}).get("name", r["template"])
                    rel_time = format_relative_time(r["last_edited"])
                    
                    # Fetch compiled PDF base64 for real preview thumbnail
                    pdf_b64 = get_pdf_base64_for_resume(r)
                    
                    with st.container(border=True):
                        # Render Thumbnail component
                        render_pdf_thumbnail(pdf_b64, key=f"thumb_{idx}")
                        
                        # Editable title input directly on the card
                        new_title = st.text_input(
                            "Rename",
                            value=r["title"],
                            key=f"ren_input_{idx}",
                            label_visibility="collapsed",
                            placeholder="Resume Title"
                        )
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
                            
                        st.markdown(f'<div style="font-size: 0.72rem; color: #64748B; margin-top: -8px; margin-bottom: 8px;">Theme: {tpl_disp} &middot; Edited {rel_time}</div>', unsafe_allow_html=True)
                        
                        # Action Row directly visible
                        c_edit, c_dl, c_dup, c_del = st.columns([3.0, 3.2, 1.4, 1.4])
                        with c_edit:
                            if st.button("✏️ Edit", key=f"btn_edit_res_{idx}", use_container_width=True, type="primary"):
                                load_active_resume(r["path"])
                                st.session_state.navigation_page = "workspace"
                                st.session_state.editor_step = 0
                                st.rerun()
                        with c_dl:
                            pdf_path = r["path"].replace(".json", ".pdf")
                            if os.path.exists(pdf_path):
                                with open(pdf_path, "rb") as pf:
                                    pdf_data = pf.read()
                                safe_title = re.sub(r"[^a-zA-Z0-9]", "_", r["title"])
                                st.download_button(
                                    "📥 PDF",
                                    data=pdf_data,
                                    file_name=f"{safe_title}_Resume.pdf",
                                    mime="application/pdf",
                                    key=f"btn_dl_res_{idx}",
                                    use_container_width=True
                                )
                            else:
                                st.button("📥 PDF", key=f"btn_dl_res_disabled_{idx}", disabled=True, use_container_width=True)
                        with c_dup:
                            if st.button("👥", key=f"btn_dup_res_{idx}", help="Duplicate Resume", use_container_width=True):
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
                        with c_del:
                            is_root = (os.path.abspath(r["path"]) == os.path.abspath(os.path.join(PROJECT_ROOT, "resume.json")))
                            if st.button("🗑️", key=f"btn_del_res_{idx}", help="Delete Resume", disabled=is_root, use_container_width=True):
                                if os.path.exists(r["path"]):
                                    os.remove(r["path"])
                                pdf_file_path = r["path"].replace(".json", ".pdf")
                                if os.path.exists(pdf_file_path):
                                    os.remove(pdf_file_path)
                                st.rerun()




# ═══════════════════════════════════════════════════════
# ③ ROUTING AND MAIN LAYOUT
# ═══════════════════════════════════════════════════════
# Autosave changes immediately
live = collect_resume()
if live != st.session_state.resume:
    push_undo(st.session_state.resume)
    st.session_state.resume = live
    st.session_state.last_hash = ""
    save_to_disk(live)
    
d   = st.session_state.resume
C   = st.session_state.color
M   = st.session_state.margins
FS  = st.session_state.fscale
FT  = st.session_state.fitting
TID = st.session_state.template

# Route check immediately stops the page if we are on My Resumes Home
if st.session_state.navigation_page in ("dashboard", "home"):
    show_home()
    st.stop()

if st.session_state.navigation_page == "career":
    st.session_state.navigation_page = "workspace"
    st.session_state.workspace_tab = "Insights"
    st.rerun()

if st.session_state.get("show_import", False):
    st.session_state.show_import = False
    show_import_dialog()

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


def format_repo_date(updated_at: str) -> str:
    if not updated_at:
        return "Unknown"
    try:
        from datetime import datetime
        parsed = datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%SZ")
        return parsed.strftime("%b %d, %Y")
    except Exception:
        return updated_at


def generate_resume_bullet(repo: dict) -> str:
    tech = repo.get("tech") or repo.get("language") or "open-source technologies"
    topics = repo.get("topics", [])
    tag_text = f" using {tech}"
    if topics:
        tag_text = f" using {tech} with {', '.join(topics[:3])}"
    desc = repo.get("description") or "a public GitHub repository."
    return f"Designed, built, and maintained the {repo['name']} repository{tag_text}, delivering business value through {desc}" 


def build_repo_card_html(repo: dict) -> str:
    description = repo.get("description") or "No description provided."
    topics = repo.get("topics", [])
    topic_html = "".join(f'<span class="repo-chip">{t}</span>' for t in topics[:4])
    language = repo.get("tech") or repo.get("language") or "Unknown"
    updated = format_repo_date(repo.get("updated_at"))
    return (
        f'<div class="repo-card">'
        f'  <div class="repo-card-header">'
        f'    <div>'
        f'      <div class="repo-card-title">{repo["name"]}</div>'
        f'      <div class="repo-card-description">{description}</div>'
        f'    </div>'
        f'    <div class="repo-score-badge">Impact {repo.get("impact_score", 0)}%</div>'
        f'  </div>'
        f'  <div class="repo-card-meta">'
        f'    <span class="repo-chip">{language}</span>'
        f'    <span class="repo-chip">Updated {updated}</span>'
        f'    <span class="repo-chip">⭐ {repo.get("stars", 0)}</span>'
        f'  </div>'
        f'  <div class="repo-card-description">{description}</div>'
        f'  <div class="repo-card-meta">{topic_html}</div>'
        f'  <div class="repo-card-footer">'
        f'    <a href="{repo.get("url")}" target="_blank">View on GitHub</a>'
        f'  </div>'
        f'</div>'
    )


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

# Determine columns layout dynamically based on current page view
workspace_tab = st.session_state.get("workspace_tab", "Edit")
# DEBUG: show current navigation/workspace state (temporary)
# st.markdown(f"**DEBUG:** navigation_page=`{st.session_state.get('navigation_page')}`, workspace_tab=`{workspace_tab}`, editor_step=`{st.session_state.get('editor_step')}`")


if workspace_tab == "Preview":
    left_col = None
    right_col = st.container()
elif workspace_tab == "Insights":
    left_col = st.container()
    right_col = None
else:  # Edit tab
    if current_step < 5:
        left_col, right_col = st.columns([2.3, 1.0], gap="medium")
    else:
        left_col, right_col = st.columns([1.0, 1.0], gap="medium")

# LEFT PANEL — Form Editor or Insights
if left_col:
    with left_col:
        if workspace_tab == "Insights":
            show_career_center()
        else:  # Edit tab
            # Sub-header Stepper widget
            st.markdown('<div id="sub-header-marker"></div>', unsafe_allow_html=True)
            sc_meta, sc_s1, sc_s2, sc_s3, sc_s4, sc_s5, sc_s6 = st.columns(
                [3.5, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6], gap="small"
            )
            with sc_meta:
                st.markdown(
                    f'<div style="display: flex; flex-direction: column; justify-content: center; height: 55px; line-height: 1.25;">'
                    f'  <span style="font-size: 0.72rem; font-weight: 700; color: #6366F1; text-transform: uppercase; letter-spacing: 0.05em;">Step {current_step + 1} of 6: {step_title}</span>'
                    f'  <span style="font-size: 0.82rem; font-weight: 600; color: #1E293B; margin-top: 1px;">{step_subtitle}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            step_cols = [sc_s1, sc_s2, sc_s3, sc_s4, sc_s5, sc_s6]
            for idx_step, col_step in enumerate(step_cols):
                with col_step:
                    is_current = (current_step == idx_step)
                    def set_step(step_num):
                        save_checkpoint(get_profile_path(), st.session_state.resume)
                        st.session_state.editor_step = step_num
                    
                    st.button(
                        str(idx_step + 1),
                        key=f"stepper_btn_{idx_step}",
                        type="primary" if is_current else "secondary",
                        use_container_width=True,
                        help=f"Go to {WIZARD_STEPS[idx_step][1]}",
                        on_click=set_step,
                        args=(idx_step,)
                    )
                    label_class = "step-label active" if is_current else "step-label"
                    st.markdown(
                        f'<div class="{label_class}">{WIZARD_STEPS[idx_step][1]}</div>',
                        unsafe_allow_html=True
                    )

            st.markdown('<div style="height: 15px;"></div>', unsafe_allow_html=True)

            # RENDER ACTIVE STEP FORM
            if current_step == 0:
                p = d.get("personal", {})
                st.markdown('<div class="sec-title">Personal Details</div>', unsafe_allow_html=True)
                cc1, cc2 = st.columns(2)
                with cc1:
                    st.text_input("Full Name *",   p.get("name",""),     key="f_nm")
                    st.text_input("Professional Title", p.get("title",""), key="f_title", placeholder="e.g. Senior Software Engineer")
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
                
                port = p.get("portfolio", {})
                pc1, pc2 = st.columns(2)
                with pc1: st.text_input("Portfolio Label", port.get("display", ""), key="f_portd", placeholder="e.g. portfolio.com")
                with pc2: st.text_input("Portfolio URL", port.get("url", ""), key="f_portu", placeholder="e.g. https://portfolio.com")

                st.markdown('<div class="sec-title">Professional Summary</div>', unsafe_allow_html=True)
                st.caption("Recommended: 40–80 words · Your career focus & top strength.")
                st.text_area("Summary", d.get("summary",""), height=110,
                             label_visibility="collapsed", key="f_summ")
                
                summary_text = st.session_state.get("f_summ", d.get("summary",""))
                word_count = len(summary_text.split()) if summary_text else 0
                char_count = len(summary_text) if summary_text else 0
                st.markdown(f"<div style='text-align: right; font-size: 0.75rem; color: #64748B; margin-top: -10px; margin-bottom: 10px;'>Words: <b>{word_count}</b> / 80 &middot; Characters: <b>{char_count}</b></div>", unsafe_allow_html=True)

                st.markdown('<div class="sec-title">Achievements</div>', unsafe_allow_html=True)
                st.caption("One achievement per line. Recommended: 3–5 items.")
                st.text_area("Achievements", "\n".join(d.get("achievements",[])),
                             height=90, label_visibility="collapsed", key="f_ach")

            elif current_step == 1:
                st.markdown('<div class="sec-title">Academic History</div>', unsafe_allow_html=True)
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

            elif current_step == 2:
                st.markdown('<div class="sec-title">Work Experience</div>', unsafe_allow_html=True)
                ec1, ec2 = st.columns(2)
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

                        # Inline Achievement Quantifier (Phase 4)
                        bullets_val = st.session_state.get(f"f_eb{i}", "\n".join(exp.get("bullets", [])))
                        lines = [line.strip() for line in bullets_val.split("\n") if line.strip()]
                        first_weak = None
                        first_weak_idx = -1
                        for l_idx, line in enumerate(lines):
                            if not AchievementQuantifier.contains_number(line):
                                first_weak = line
                                first_weak_idx = l_idx
                                break
                        if first_weak:
                            sug = AchievementQuantifier.generate_suggestion(first_weak)
                            if sug:
                                st.markdown(
                                    f'<div style="background:#FFFBEB; border-left:4px solid #F59E0B; padding:10px; border-radius:6px; margin: 10px 0;">'
                                    f'<div style="font-weight:700; color:#B45309; font-size:0.85rem;">💡 Make This Stronger</div>'
                                    f'<div style="font-size:0.8rem; color:#78350F; margin-top:2px;"><b>Original:</b> "{first_weak}"</div>'
                                    f'<div style="font-size:0.8rem; color:#78350F; margin-top:2px;"><b>Suggestion:</b> "{sug["improved"]}"</div>'
                                    f'<div style="font-size:0.75rem; color:#92400E; margin-top:4px; font-style:italic;">{sug["reason"]}</div>'
                                    f'</div>',
                                    unsafe_allow_html=True
                                )
                                if st.button("Apply Suggestion", key=f"apply_sug_exp_{i}", type="secondary", use_container_width=True):
                                    lines[first_weak_idx] = sug["improved"]
                                    st.session_state[f"f_eb{i}"] = "\n".join(lines)
                                    st.rerun()

            elif current_step == 3:
                st.markdown('<div class="sec-title">Projects</div>', unsafe_allow_html=True)
                pc1, pc2 = st.columns(2)
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

                # Inline GitHub Import (Phase 3)
                with st.expander("🐙 Import from GitHub", expanded=True):
                    if not st.session_state.get("github_username"):
                        st.write("Connect your GitHub account to import repositories directly.")
                        user_in = st.text_input("GitHub Username", key="inline_gh_user_input")

                        def connect_github():
                            if st.session_state.inline_gh_user_input.strip():
                                st.session_state.github_username = st.session_state.inline_gh_user_input.strip()

                        if st.button("Connect & Fetch Repositories", key="inline_gh_connect", type="primary", use_container_width=True, on_click=connect_github):
                            pass
                    else:
                        st.write(f"Connected to GitHub as **{st.session_state.github_username}**")

                        def clear_github_username():
                            st.session_state.github_username = ""

                        if st.button("Change Username", key="inline_gh_change_user", use_container_width=True, on_click=clear_github_username):
                            pass

                        gh_analysis = GitHubIntegration.analyze_profile(st.session_state.github_username)
                        projs = gh_analysis.get("suggested_projects", [])
                        if projs:
                            languages = ["All"] + sorted({(p.get("tech") or p.get("language") or "Unknown") for p in projs})
                            topics = sorted({t for p in projs for t in p.get("topics", []) if t})
                            if "gh_repo_search" not in st.session_state:
                                st.session_state.gh_repo_search = ""
                            if "gh_repo_sort" not in st.session_state:
                                st.session_state.gh_repo_sort = "Impact score"
                            if "gh_repo_lang_filter" not in st.session_state:
                                st.session_state.gh_repo_lang_filter = "All"
                            if "gh_repo_topic_filter" not in st.session_state:
                                st.session_state.gh_repo_topic_filter = []

                            c1, c2, c3 = st.columns([3, 2, 2], gap="small")
                            with c1:
                                st.text_input("Search repositories", key="gh_repo_search", placeholder="Search by name, description, language, topic...")
                            with c2:
                                st.selectbox("Sort by", ["Impact score", "Stars", "Last updated", "Name"], key="gh_repo_sort")
                            with c3:
                                st.selectbox("Filter by language", languages, key="gh_repo_lang_filter")

                            c4, c5 = st.columns([3, 2], gap="small")
                            with c4:
                                st.multiselect("Filter by topics", topics, key="gh_repo_topic_filter")
                            with c5:
                                if st.button("Reset filters", key="gh_repo_reset", use_container_width=True, type="secondary"):
                                    st.session_state.gh_repo_search = ""
                                    st.session_state.gh_repo_sort = "Impact score"
                                    st.session_state.gh_repo_lang_filter = "All"
                                    st.session_state.gh_repo_topic_filter = []

                            query = st.session_state.gh_repo_search.strip().lower()
                            lang_filter = st.session_state.gh_repo_lang_filter
                            topic_filter = st.session_state.gh_repo_topic_filter

                            filtered_repos = []
                            for repo in projs:
                                combined = " ".join([
                                    repo.get("name", ""),
                                    repo.get("description", "") or "",
                                    str(repo.get("tech") or repo.get("language") or ""),
                                    " ".join(repo.get("topics", []))
                                ]).lower()
                                if query and query not in combined:
                                    continue
                                if lang_filter != "All" and (repo.get("tech") or repo.get("language") or "Unknown") != lang_filter:
                                    continue
                                if topic_filter and not any(t in repo.get("topics", []) for t in topic_filter):
                                    continue
                                filtered_repos.append(repo)

                            sort_key = st.session_state.gh_repo_sort
                            if sort_key == "Impact score":
                                filtered_repos.sort(key=lambda x: x.get("impact_score", 0), reverse=True)
                            elif sort_key == "Stars":
                                filtered_repos.sort(key=lambda x: x.get("stars", 0), reverse=True)
                            elif sort_key == "Last updated":
                                filtered_repos.sort(key=lambda x: x.get("updated_at") or "", reverse=True)
                            else:
                                filtered_repos.sort(key=lambda x: x.get("name", ""))

                            recommended = [repo for repo in filtered_repos if repo.get("impact_score", 0) >= 55][:6]
                            if not recommended and filtered_repos:
                                recommended = filtered_repos[:min(4, len(filtered_repos))]
                            other_repos = [repo for repo in filtered_repos if repo not in recommended]

                            st.markdown("<div style='margin-top:12px; margin-bottom:8px; font-size:0.96rem; color:#475569;'>Choose the best repositories to add to your resume. Higher Impact Score means stronger resume value.</div>", unsafe_allow_html=True)

                            if recommended:
                                st.markdown("<div style='font-weight:700; font-size:0.95rem; margin-bottom:4px;'>Recommended For Resume</div>", unsafe_allow_html=True)
                                for idx in range(0, len(recommended), 3):
                                    cols = st.columns(3, gap="medium")
                                    for col, repo in zip(cols, recommended[idx:idx+3]):
                                        with col:
                                            st.markdown(build_repo_card_html(repo), unsafe_allow_html=True)
                                            if st.button("Add To Resume", key=f"gh_add_rec_{repo['name']}_{idx}", use_container_width=True):
                                                new_proj = {
                                                    "title": repo["name"],
                                                    "link": repo["url"],
                                                    "date": "Present",
                                                    "tools": ", ".join([t for t in [repo.get("tech") or repo.get("language"), *repo.get("topics", [])] if t]),
                                                    "bullets": [generate_resume_bullet(repo)],
                                                }
                                                push_undo(d)
                                                d.setdefault("projects", []).append(new_proj)
                                                personal = d.setdefault("personal", {})
                                                github = personal.setdefault("github", {})
                                                if not github.get("display"):
                                                    github["display"] = st.session_state.github_username
                                                if not github.get("url"):
                                                    github["url"] = f"https://github.com/{st.session_state.github_username}"
                                                save_to_disk(d)
                                                st.session_state.resume = d
                                                st.session_state.last_hash = ""
                                                st.success(f"✅ Added {repo['name']} to your resume")

                            if other_repos:
                                st.markdown("<div style='font-weight:700; font-size:0.95rem; margin:18px 0 6px;'>Other Repositories</div>", unsafe_allow_html=True)
                                for idx in range(0, len(other_repos), 3):
                                    cols = st.columns(3, gap="medium")
                                    for col, repo in zip(cols, other_repos[idx:idx+3]):
                                        with col:
                                            st.markdown(build_repo_card_html(repo), unsafe_allow_html=True)
                                            if st.button("Add To Resume", key=f"gh_add_other_{repo['name']}_{idx}", use_container_width=True):
                                                new_proj = {
                                                    "title": repo["name"],
                                                    "link": repo["url"],
                                                    "date": "Present",
                                                    "tools": ", ".join([t for t in [repo.get("tech") or repo.get("language"), *repo.get("topics", [])] if t]),
                                                    "bullets": [generate_resume_bullet(repo)],
                                                }
                                                push_undo(d)
                                                d.setdefault("projects", []).append(new_proj)
                                                personal = d.setdefault("personal", {})
                                                github = personal.setdefault("github", {})
                                                if not github.get("display"):
                                                    github["display"] = st.session_state.github_username
                                                if not github.get("url"):
                                                    github["url"] = f"https://github.com/{st.session_state.github_username}"
                                                save_to_disk(d)
                                                st.session_state.resume = d
                                                st.session_state.last_hash = ""
                                                st.success(f"✅ Added {repo['name']} to your resume")

                        else:
                            st.warning("No public repositories found.")

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

                        # Inline Achievement Quantifier (Phase 4)
                        bullets_val = st.session_state.get(f"f_pb{i}", "\n".join(pr.get("bullets", [])))
                        lines = [line.strip() for line in bullets_val.split("\n") if line.strip()]
                        first_weak = None
                        first_weak_idx = -1
                        for l_idx, line in enumerate(lines):
                            if not AchievementQuantifier.contains_number(line):
                                first_weak = line
                                first_weak_idx = l_idx
                                break
                        if first_weak:
                            sug = AchievementQuantifier.generate_suggestion(first_weak)
                            if sug:
                                st.markdown(
                                    f'<div style="background:#FFFBEB; border-left:4px solid #F59E0B; padding:10px; border-radius:6px; margin: 10px 0;">'
                                    f'<div style="font-weight:700; color:#B45309; font-size:0.85rem;">💡 Make This Stronger</div>'
                                    f'<div style="font-size:0.8rem; color:#78350F; margin-top:2px;"><b>Original:</b> "{first_weak}"</div>'
                                    f'<div style="font-size:0.8rem; color:#78350F; margin-top:2px;"><b>Suggestion:</b> "{sug["improved"]}"</div>'
                                    f'<div style="font-size:0.75rem; color:#92400E; margin-top:4px; font-style:italic;">{sug["reason"]}</div>'
                                    f'</div>',
                                    unsafe_allow_html=True
                                )
                                if st.button("Apply Suggestion", key=f"apply_sug_proj_{i}", type="secondary", use_container_width=True):
                                    lines[first_weak_idx] = sug["improved"]
                                    st.session_state[f"f_pb{i}"] = "\n".join(lines)
                                    st.rerun()

            elif current_step == 4:
                st.markdown('<div class="sec-title">Technical Skills</div>', unsafe_allow_html=True)
                sk = d.get("technical_skills",{})
                keys_list = list(sk.keys())
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
                            for k3 in ["f_ncat", "f_nval"]:
                                if k3 in st.session_state: del st.session_state[k3]
                            st.rerun()

                # Smart Skill Suggestions (Phase 5)
                target_role = st.session_state.get("target_role", "Frontend Developer")
                gap_res = CareerGapAnalyzer.analyze(d, target_role)
                missing_skills = gap_res.get("missing", [])
                if missing_skills:
                    st.markdown("##### 💡 Recommended Skills to Add")
                    st.caption(f"Based on target role: **{target_role}** (Configure in Insights tab)")
                    selected_missing = st.multiselect("Select skills to append:", options=missing_skills, key="missing_skills_multiselect")
                    if selected_missing and st.button("Add Selected Skills", key="add_missing_skills_btn", type="primary", use_container_width=True):
                        sk = d.setdefault("technical_skills", {})
                        if not sk:
                            sk["Languages & Frameworks"] = ""
                        first_cat = list(sk.keys())[0]
                        current_val = sk[first_cat]
                        if current_val.strip():
                            new_val = current_val.rstrip(" ,") + ", " + ", ".join(selected_missing)
                        else:
                            new_val = ", ".join(selected_missing)
                        
                        push_undo(d)
                        sk[first_cat] = new_val
                        save_to_disk(d)
                        st.session_state.resume = d
                        st.session_state.last_hash = ""
                        st.success(f"✅ Added {', '.join(selected_missing)} to {first_cat}!")
                        st.rerun()

                st.markdown('<div class="sec-title">Certifications</div>', unsafe_allow_html=True)
                st.caption("One certification per line.")
                st.text_area("Certifications", "\n".join(d.get("certifications",[])),
                             height=90, label_visibility="collapsed", key="f_cert")

            elif current_step == 5:
                # STEP 5: Review & Finish
                # Render templates gallery visual grid
                st.markdown('<div class="sec-title">Select Design Theme</div>', unsafe_allow_html=True)
                st.caption("Choose a curated template style. The live preview updates instantly.")

                TPL_INFOS = {
                    "sejal_original": {"name": "Modern Accent", "desc": "Clean typography with subtle color accents.", "icon": "🎨", "color": "#6366F1"},
                    "ats":            {"name": "ATS Professional", "desc": "Industry-standard, highly scannable layout.", "icon": "💼", "color": "#1E293B"},
                    "modern":         {"name": "Elegant Modern", "desc": "Stylish sans-serif theme with modern headings.", "icon": "✨", "color": "#0F766E"},
                    "creative":       {"name": "Creative Bold", "desc": "Vibrant design to stand out in creative roles.", "icon": "🚀", "color": "#E11D48"},
                    "minimal":        {"name": "Minimalist Clean", "desc": "Simple, elegant spacing focusing on content.", "icon": "📄", "color": "#475569"},
                    "two_column":     {"name": "Two Column Splitted", "desc": "Balanced two-column split layout.", "icon": "📊", "color": "#7C3AED"}
                }

                g_cols = st.columns(3, gap="small")
                for i, (tpl_id, info) in enumerate(TPL_INFOS.items()):
                    col = g_cols[i % 3]
                    with col:
                        is_selected = (TID == tpl_id)
                        border_css = f"border: 2px solid {info['color'] if is_selected else '#E2E8F0'};"
                        bg_css = f"background: {info['color']}08;" if is_selected else "background: #FFFFFF;"
                        shadow_css = "box-shadow: 0 4px 12px rgba(99,102,241,0.12);" if is_selected else "box-shadow: 0 1px 3px rgba(0,0,0,0.02);"
                        
                        st.markdown(
                            f'<div style="{border_css} {bg_css} {shadow_css} border-radius: 12px; padding: 12px; height: 180px; display: flex; flex-direction: column; justify-content: space-between; transition: all 0.2s ease;">'
                            f'  <div>'
                            f'    <div style="display: flex; align-items: center; gap: 8px;">'
                            f'      <span style="font-size: 1.4rem;">{info["icon"]}</span>'
                            f'      <span style="font-weight: 700; font-size: 0.85rem; color: #1E293B;">{info["name"]}</span>'
                            f'    </div>'
                            f'    <p style="font-size: 0.72rem; color: #64748B; margin-top: 6px; line-height: 1.3;">{info["desc"]}</p>'
                            f'  </div>'
                            f'  <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; height: 65px; padding: 6px; display: flex; flex-direction: column; gap: 4px;">'
                            f'    <div style="height: 5px; width: 25px; background: {info["color"]}; border-radius: 1px;"></div>'
                            f'    <div style="height: 2px; width: 100%; background: #E2E8F0; border-radius: 0.5px;"></div>'
                            f'    <div style="display: flex; gap: 4px;">'
                            f'      <div style="height: 35px; width: {"50%" if tpl_id == "two_column" else "100%"}; background: white; border: 0.5px solid #E2E8F0; border-radius: 2px; padding: 3px; display: flex; flex-direction: column; gap: 2.5px;">'
                            f'        <div style="height: 2px; width: 80%; background: #F1F5F9;"></div>'
                            f'        <div style="height: 1.5px; width: 90%; background: #F8FAFC;"></div>'
                            f'        <div style="height: 1.5px; width: 70%; background: #F8FAFC;"></div>'
                            f'      </div>'
                            f'      {"<div style=\'height: 35px; width: 50%; background: white; border: 0.5px solid #E2E8F0; border-radius: 2px; padding: 3px; display: flex; flex-direction: column; gap: 2.5px;\'><div style=\'height: 2px; width: 70%; background: #F1F5F9;\'></div></div>" if tpl_id == "two_column" else ""}'
                            f'    </div>'
                            f'  </div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                        btn_txt = "Active Theme" if is_selected else "Select"
                        if st.button(btn_txt, key=f"select_tpl_{tpl_id}", type="primary" if is_selected else "secondary", use_container_width=True):
                            st.session_state.template = tpl_id
                            st.session_state.last_hash = ""
                            save_to_disk(st.session_state.resume)
                            st.rerun()

                st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
                st.markdown('<div class="sec-title">Page Layout Settings</div>', unsafe_allow_html=True)
                
                new_m = st.slider("Margin (pt)", 10, 36, M, 2, key="adv_mg")
                m_txt, m_cls = margin_label(new_m)
                st.markdown(f'Current: <b>{new_m}pt</b> &rarr; <span class="setting-effect {m_cls}">{m_txt}</span>', unsafe_allow_html=True)
                
                new_fs = st.slider("Font Scale", 0.75, 1.25, FS, 0.05, key="adv_fs")
                fs_txt, fs_cls = fscale_label(new_fs)
                st.markdown(f'Current: <b>{new_fs:.2f}×</b> &rarr; <span class="setting-effect {fs_cls}">{fs_txt}</span>', unsafe_allow_html=True)
                
                new_ft = st.radio("Page Fitting", FITTING_OPTS, index=FITTING_OPTS.index(FT), key="adv_fit", horizontal=True)
                
                if (new_m != M) or (new_fs != FS) or (new_ft != FT):
                    st.session_state.margins = new_m
                    st.session_state.fscale = new_fs
                    st.session_state.fitting = new_ft
                    st.session_state.last_hash = ""
                    st.rerun()

                st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
                st.markdown('<div class="sec-title">Web Portfolio</div>', unsafe_allow_html=True)
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

            # --- CONTEXT-AWARE COMPLETION BANNER (PHASE 2) ---
            step_is_done = _step_done(current_step, d)
            if step_is_done:
                # Determine section-specific improvement tips
                _tips_map = {
                    0: ["Ensure your professional title matches target jobs.", "Keep summary between 40–80 words.", "Bullet achievements with strong metrics."],
                    1: ["List your latest degree first.", "Add grade/CGPA if above 3.5 or top of class.", "Include relevant coursework or projects."],
                    2: ["Use action verbs: Designed, Built, Led, Reduced.", "Quantify every bullet with a metric or percentage.", "List most recent job first."],
                    3: ["Link to a working demo or GitHub repo.", "Explain the architecture decision — why you chose the tech.", "List tools/technologies used prominently."],
                    4: ["Only list skills you can answer interview questions on.", "Categorize logically: Languages, Frameworks, Tools, Cloud.", "Keep 5–15 skills per category."],
                }
                _tips = _tips_map.get(current_step, [])

                st.markdown(
                    f'<div style="background:#ECFDF5; border-left:4px solid #10B981; padding:12px 14px; border-radius:8px; margin: 15px 0 8px;">'
                    f'<span style="font-weight:700; color:#065F46; font-size:0.88rem;">✅ {step_title} Section Completed</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                if _tips:
                    with st.expander("💡 Tips to improve this section", expanded=False):
                        for tip in _tips:
                            st.markdown(f"- {tip}")
                
                improve_col, quality_col = st.columns(2)
                with quality_col:
                    if st.button("📊 Check Resume Quality", key="step_check_quality_btn", use_container_width=True):
                        st.session_state.workspace_tab = "Insights"
                        st.rerun()

            # --- PREVIOUS / NEXT STEP BUTTONS ---
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
                        st.session_state.editor_step = current_step + 1
                        st.rerun()
                else:
                    if st.button("🏠 Go Home", key="wz_finish_btn", use_container_width=True, type="primary"):
                        st.session_state.navigation_page = "home"
                        st.rerun()

# RIGHT COLUMN (Sticky Live Preview)
if right_col:
    with right_col:
        st.markdown('<div id="right-panel-anchor"></div>', unsafe_allow_html=True)
        st.markdown("""
        <style>
        @media (min-width: 768px) {
          [data-testid="column"]:has(#right-panel-anchor) {
            position: sticky;
            top: 2rem;
            align-self: flex-start;
            max-height: calc(100vh - 4rem);
            overflow-y: auto;
          }
          [data-testid="column"]:has(#right-panel-anchor)::-webkit-scrollbar { width: 6px; }
          [data-testid="column"]:has(#right-panel-anchor)::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 10px; }
        }
        </style>
        """, unsafe_allow_html=True)

        hs = calculate_health_score(d)
        score = hs["score"]

        # 🤖 Resume Coach Card
        st.markdown(
            f'<div style="background: #FFFFFF; border: 1.5px solid {"#E2E8F0" if score >= 80 else "#FEF3C7"}; '
            f'border-radius: 12px; padding: 16px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">'
            f'<div style="display: flex; align-items: center; gap: 8px;">'
            f'<span style="font-size: 1.3rem;">🤖</span>'
            f'<span style="font-weight: 800; font-size: 1.05rem; color: #1E293B;">Resume Coach</span>'
            f'</div>'
            f'<div style="margin-top: 8px; font-size: 0.85rem; color: #64748B;">'
            f'Resume Health Score: <strong style="color: {"#10B981" if score >= 80 else "#D97706"}; font-size: 1.1rem;">{score}%</strong>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        if score < 80:
            st.markdown("##### ⚠️ Suggestions to improve:")
            sugs = hs.get("suggestions", [])[:3]
            if not sugs:
                st.write("No suggestions found.")
            else:
                for idx, s in enumerate(sugs):
                    st.markdown(
                        f'<div style="background:#FFFDF5; border-left:3px solid #F59E0B; padding:8px 10px; border-radius:4px; margin-bottom:8px; font-size:0.8rem; color:#78350F;">'
                        f'{s}'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                    # Navigation mapping
                    target_step = 0
                    s_lower = s.lower()
                    if "education" in s_lower: target_step = 1
                    elif "experience" in s_lower or "jobs" in s_lower: target_step = 2
                    elif "project" in s_lower: target_step = 3
                    elif "skill" in s_lower: target_step = 4
                    elif "summary" in s_lower: target_step = 0
                    
                    if st.button("Fix Now", key=f"coach_fix_{idx}", use_container_width=True):
                        st.session_state.editor_step = target_step
                        st.rerun()
        else:
            # Milestone banner
            st.markdown(
                f'<div style="background:#ECFDF5; border-left:4px solid #10B981; padding:12px; border-radius:8px; margin-bottom:12px;">'
                f'<span style="font-weight:700; color:#065F46; font-size:0.9rem;">🎉 Resume {score}% Complete!</span><br/>'
                f'<span style="color:#047857; font-size:0.78rem;">You have unlocked the Career Assistant tools.</span>'
                f'</div>',
                unsafe_allow_html=True
            )
            
            st.markdown("##### 📋 Recommended Final Checks")
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                if st.button("ATS Check", key=f"fc_ats", use_container_width=True, help="Run ATS Check"):
                    st.session_state.workspace_tab = "Insights"
                    st.session_state.career_active_tool = "consistency"
                    st.rerun()
            with fc2:
                if st.button("Consistency", key=f"fc_const", use_container_width=True, help="Review Consistency"):
                    st.session_state.workspace_tab = "Insights"
                    st.session_state.career_active_tool = "consistency"
                    st.rerun()
            with fc3:
                if st.button("Prep Interview", key=f"fc_prep", use_container_width=True, help="Prepare Interview"):
                    st.session_state.workspace_tab = "Insights"
                    st.session_state.career_active_tool = "interview_prep"
                    st.rerun()
            
            st.markdown("##### 🚀 Guided Career Assistant")
            gc_col1, gc_col2 = st.columns(2)
            with gc_col1:
                if st.button("🚀 Improve Resume", key="ca_improve_res", use_container_width=True):
                    st.session_state.workspace_tab = "Insights"
                    st.session_state.career_active_tool = "consistency"
                    st.rerun()
                if st.button("📈 Analyze Skill Gaps", key="ca_skill_gaps", use_container_width=True):
                    st.session_state.workspace_tab = "Insights"
                    st.session_state.career_active_tool = "gap_analyzer"
                    st.rerun()
            with gc_col2:
                if st.button("💼 Prep Interviews", key="ca_prep_int", use_container_width=True):
                    st.session_state.workspace_tab = "Insights"
                    st.session_state.career_active_tool = "interview_prep"
                    st.rerun()
                if st.button("🐙 Verify GitHub Evidence", key="ca_github_ev", use_container_width=True):
                    st.session_state.workspace_tab = "Insights"
                    st.session_state.career_active_tool = "github"
                    st.rerun()
        
        st.markdown("<hr style='margin: 15px 0; border: 0.5px solid #E2E8F0;'/>", unsafe_allow_html=True)

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

        with st.spinner("🔄 Updating preview…"):
            try:
                maybe_compile(d, TID, C, M, FS, FT)
            except Exception as compile_err:
                st.session_state.cok = False
                st.session_state.cmsg = f"Compilation error: {compile_err}"

        if st.session_state.cmsg:
            st.warning(f"⚠️ {st.session_state.cmsg}")

        if st.session_state.cok and st.session_state.pdf_b64:
            is_mobile_view = (st.session_state.get("device_view", "desktop") == "mobile")
            mobile_style_css = ".page-wrapper { max-width: 360px !important; margin: 0 auto !important; }" if is_mobile_view else ""
            
            pdf_b64 = st.session_state.pdf_b64
            pdf_js_b64, pdf_worker_b64 = load_local_pdfjs_assets()
            pdf_html = f"""<!DOCTYPE html>
<html>
<head>
<script>
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

  const wrapper = document.createElement('div');
  wrapper.className = 'page-wrapper';
  wrapper.style.maxWidth = (vp.width / SCALE) + 'px';
  wrapper.style.width = '100%';

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

    pass

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
    
    bf_tools, bf_dl = st.columns([1, 1])
    
    with bf_tools:
        with st.popover("✨ More Actions", use_container_width=True):
            st.markdown("### Resume Utilities")
            if st.button("📥 Import Resume", key="fbar_import", use_container_width=True):
                st.session_state.show_import = True
                st.rerun()
            if st.button("📊 Open Insights", key="fbar_open_ins", use_container_width=True):
                st.session_state.workspace_tab = "Insights"
                st.session_state.navigation_page = "workspace"
                st.rerun()
            if st.button("📥 Demo Resume", key="fbar_demo", use_container_width=True):
                st.session_state.resume = copy.deepcopy(DEMO_RESUME)
                st.session_state.last_hash = ""
                save_to_disk(st.session_state.resume)
                st.rerun()
            if st.button("🔄 Reset Form", key="fbar_reset", use_container_width=True):
                st.session_state.resume = copy.deepcopy(DEFAULT)
                st.session_state.last_hash = ""
                save_to_disk(st.session_state.resume)
                st.rerun()
            
    with bf_dl:
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
