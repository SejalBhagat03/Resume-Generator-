# -*- coding: utf-8 -*-
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
import os
os.environ.setdefault("SCRIPT_RUN_CONTEXT", "1")


import streamlit as st
import json, os, base64, re, time, copy
# Ensure the top-level 'core' package is importable and that the local
# resume_builder/ directory takes import precedence over the root directory
# to prevent namespace conflicts (e.g. services.ai vs root services/).
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.pdf_engine import build_pdf
from resume_builder.templates import TEMPLATES, register_templates
from resume_builder.services.ai import calculate_health_score
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
from resume_builder.services.ai import AchievementQuantifier, CareerGapAnalyzer
from resume_builder.services.github import GitHubIntegration
from resume_builder.ui.wizard_ui import render_wizard_header, render_wizard_stepper, render_profile_type_cards, render_import_cards
from resume_builder.components.navbar import render_navbar
from resume_builder.components.dialogs import show_import_dialog
from resume_builder.components.wizard import show_create_resume_dialog
from resume_builder.components.sidebar import render_sidebar
from resume_builder.components.hero import render_hero
from resume_builder.components.resume_card import render_resume_grid_card, render_continue_card_desktop, render_continue_card_mobile
from resume_builder.components.search_bar import render_search_bar_desktop, render_search_bar_mobile
from resume_builder.components.bottom_nav import render_bottom_nav
from resume_builder.pages.home import show_home
from resume_builder.pages.editor import push_undo, do_undo, do_redo, show_editor

# def render_navbar():
#     st.write("NAVBAR PLACEHOLDER")

# def render_hero():
#     st.write("HERO PLACEHOLDER")

# def render_resume_grid_card(r, tpl_disp, rel_time):
#     st.write(f"RESUME GRID CARD PLACEHOLDER: {r.get('title')}")

# def render_continue_card_desktop(latest, tpl_disp, rel_time):
#     st.write(f"CONTINUE CARD DESKTOP PLACEHOLDER: {latest.get('title')}")

# def render_continue_card_mobile(latest, tpl_disp, rel_time):
#     st.write(f"CONTINUE CARD MOBILE PLACEHOLDER: {latest.get('title')}")

# def render_search_bar_desktop(search_query):
#     st.write("SEARCH BAR DESKTOP PLACEHOLDER")

# def render_search_bar_mobile(search_query):
#     st.write("SEARCH BAR MOBILE PLACEHOLDER")

# def render_bottom_nav():
#     st.write("BOTTOM NAV PLACEHOLDER")

# def show_import_dialog():
#     st.write("IMPORT DIALOG PLACEHOLDER")

# def show_create_resume_dialog():
#     st.write("CREATE RESUME DIALOG PLACEHOLDER")

# ═══════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════
st.set_page_config(
    page_title="Resume Builder Pro",
    page_icon="&#x1F4C4;",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# CSS loading moved below after PROJECT_ROOT


# ═══════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════
# Absolute project root — works regardless of working directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESUME_JSON  = os.path.join(PROJECT_ROOT, "resume.json")
DEFAULTS_FILE = os.path.join(PROJECT_ROOT, "resume_builder", "config", "defaults.json")
# Load custom CSS (refactored split styling)
css_files = ["variables.css", "base.css", "layout.css", "components.css", "responsive.css"]
for css_file in css_files:
    css_path = os.path.join(PROJECT_ROOT, "resume_builder", "assets", css_file)
    if os.path.exists(css_path):
        with open(css_path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


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

# Function/Constant mappings to prevent circular app.py imports
_s("DEFAULT_RESUME", DEFAULT)
_s("PROJECT_ROOT", PROJECT_ROOT)


# ═══════════════════════════════════════════════════════
# DATA I/O (Imported from services/storage.py) & UTILS
# ═══════════════════════════════════════════════════════
from resume_builder.services.storage import (
    save_to_disk,
    load_from_disk,
    load_active_resume,
    get_pdf_base64_for_resume,
    list_resumes,
    load_local_pdfjs_assets,
    get_profile_metrics,
    save_checkpoint,
    get_profile_path,
)
from resume_builder.utils.helpers import margin_label, fscale_label, format_relative_time
from resume_builder.utils.validators import sanitize_html, resume_hash


# ═══════════════════════════════════════════════════════
# UNDO / REDO
# ═══════════════════════════════════════════════════════
MAX_HISTORY = 30


# Moved to utils.validators


# ═══════════════════════════════════════════════════════
# PDF COMPILE
# ═══════════════════════════════════════════════════════


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


# Helpers & Sanitizers moved to utils/helpers.py and utils/validators.py


# ═══════════════════════════════════════════════════════
# COLLECT RESUME FROM WIDGET KEYS  (live, no st.form)
# ═══════════════════════════════════════════════════════


# Function state registrations after definitions to prevent NameErrors
_s("load_active_resume_fn", load_active_resume)
_s("push_undo_fn", push_undo)
_s("save_to_disk_fn", save_to_disk)
_s("save_extracted_template_fn", save_extracted_template)
_s("load_local_pdfjs_assets_fn", load_local_pdfjs_assets)


# ═══════════════════════════════════════════════════════
# REGISTER TEMPLATES
# ═══════════════════════════════════════════════════════
register_templates()
ALL_TEMPLATES = TEMPLATES

# Load resume.json on first run
if "resume_loaded" not in st.session_state:
    load_active_resume(os.path.join(PROJECT_ROOT, "resume.json"))
    st.session_state.resume_loaded = True

# ═══════════════════════════════════════════════════════
# ROUTING CONTROLLER
# ═══════════════════════════════════════════════════════
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

# Render editor workspace
show_editor()

