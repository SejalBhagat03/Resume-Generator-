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
# Ensure the top-level 'core' package is importable when running from the
# resume_builder directory.
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.pdf_engine import build_pdf
from resume_builder.templates import TEMPLATES, register_templates
from analysis.health_scorer import calculate_health_score
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
from analysis.achievement_quantifier import AchievementQuantifier
from analysis.gap_analyzer import CareerGapAnalyzer
from services.github_service import GitHubIntegration
from resume_builder.ui.wizard_ui import render_wizard_header, render_wizard_stepper, render_profile_type_cards, render_import_cards
from components.navbar import render_navbar
from components.dialogs import show_import_dialog
from components.wizard import show_create_resume_dialog
from components.sidebar import render_sidebar
from components.hero import render_hero
from components.resume_card import render_resume_grid_card, render_continue_card_desktop, render_continue_card_mobile
from components.search_bar import render_search_bar_desktop, render_search_bar_mobile
from components.bottom_nav import render_bottom_nav

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

    # skills — only collect edits to existing rows; new category is added via the &#x2795; button
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
        if st.button("&#x2190; Resumes", key="btn_back_home", use_container_width=True, help="Back to My Resumes"):
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
            with st.popover("&#9881;&#65039;", use_container_width=True, help="Resume options"):
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
                if st.button("&#x1F5D1;&#65039; Delete", key="top_del_btn", use_container_width=True, disabled=is_root, help="Root resume cannot be deleted"):
                    if os.path.exists(get_profile_path()):
                        os.remove(get_profile_path())
                    st.session_state.current_profile_path = os.path.join(PROJECT_ROOT, "resume.json")
                    st.session_state.resume = load_from_disk()
                    st.session_state.navigation_page = "home"
                    st.rerun()
            
    with c_saved:
        st.markdown('<div style="display: flex; align-items: center; justify-content: center; height: 38px;"><span style="color: #10B981; font-weight: 700; font-size: 0.85rem;">&#10003; Saved</span></div>', unsafe_allow_html=True)
        
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
            
        with st.popover("&#128220; History", use_container_width=True, help="View and restore checkpoints"):
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
            if st.button("&#128248; Save Checkpoint", key="btn_save_cp_manual", use_container_width=True):
                save_checkpoint(get_profile_path(), st.session_state.resume)
                st.success("Checkpoint saved!")
                st.rerun()
        
    with c_edit:
        is_active_edit = (st.session_state.workspace_tab == "Edit")
        if st.button("&#9999;&#65039; Edit", key="btn_wtab_edit", type="primary" if is_active_edit else "secondary", use_container_width=True):
            st.session_state.workspace_tab = "Edit"
            st.session_state.navigation_page = "workspace"
            st.rerun()
            
    with c_prev:
        is_active_prev = (st.session_state.workspace_tab == "Preview")
        if st.button("&#128065;&#65039; Preview", key="btn_wtab_prev", type="primary" if is_active_prev else "secondary", use_container_width=True):
            st.session_state.workspace_tab = "Preview"
            st.session_state.navigation_page = "workspace"
            st.rerun()
            
    with c_ins:
        is_active_ins = (st.session_state.workspace_tab == "Insights")
        if st.button("&#x1F4CA; Insights", key="btn_wtab_ins", type="primary" if is_active_ins else "secondary", use_container_width=True):
            st.session_state.workspace_tab = "Insights"
            st.session_state.navigation_page = "workspace"
            st.rerun()
            
    with c_accent:
        COLOR_ICONS = {
            "Indigo": "&#128309; Indigo",
            "Blue": "&#128309; Blue",
            "Emerald": "&#128994; Emerald",
            "Rose": "&#128308; Rose",
            "Violet": "&#128995; Violet",
            "Slate": "&#9899; Slate",
            "Custom": "&#x1F3A8; Custom"
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






def show_home():
    """Phase 1: My Resumes Dashboard containing Recent Resumes card grid."""
    import html
    
    # 1. Hidden marker for CSS targeting
    st.markdown('<div id="dashboard-marker"></div>', unsafe_allow_html=True)
    
    # 2. Top Navigation Bar & Left Sidebar
    # NOTE: st.markdown() renders inside a Streamlit iframe, so CSS from custom.css
    # does NOT reach these elements. We embed a <style> block here for the sidebar/header
    # styles. The JS talks to window.parent to update --sidebar-w on the parent document.
    st.markdown(
        """
        <style>
        /* === Self-contained sidebar & header styles (inside Streamlit iframe) === */
        :host, body { margin: 0; padding: 0; }

        .rb-main-header {
          position: fixed;
          top: 0; left: 0; right: 0;
          height: 72px;
          background: #FFFFFF;
          border-bottom: 1px solid #E7DED4;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 24px;
          z-index: 1000;
          box-shadow: 0 2px 10px rgba(0,0,0,0.02);
          font-family: 'Inter', sans-serif;
          box-sizing: border-box;
        }
        .rb-header-left { display: flex; align-items: center; gap: 16px; }
        .rb-header-right { display: flex; align-items: center; gap: 16px; }
        .rb-hamburger {
          font-size: 1.4rem; color: #1E293B; cursor: pointer;
          padding: 6px 8px; border-radius: 6px; transition: background 0.2s;
          user-select: none; line-height: 1;
        }
        .rb-hamburger:hover { background: #F8F5EF; }
        .rb-logo { display: flex; align-items: center; gap: 8px; }
        .rb-logo-text { font-weight: 700; font-size: 1.15rem; color: #1E293B; letter-spacing: -0.02em; }
        .rb-noti { font-size: 1.3rem; cursor: pointer; padding: 6px; border-radius: 50%; color: #1E293B; }
        .rb-avatar {
          width: 36px; height: 36px; background: #A47148; color: #fff;
          border-radius: 50%; display: flex; align-items: center;
          justify-content: center; font-weight: 700; font-size: 0.9rem;
          border: 2px solid #E7DED4;
        }

        .rb-sidebar {
          position: fixed;
          top: 72px; left: 0; bottom: 0;
          width: 64px;
          background: #FFFFFF;
          border-right: 1px solid #E7DED4;
          z-index: 999;
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 16px 0;
          transition: width 0.25s cubic-bezier(0.4, 0, 0.2, 1);
          overflow: hidden;
          font-family: 'Inter', sans-serif;
        }
        .rb-sidebar.expanded {
          width: 240px;
          align-items: flex-start;
          padding: 16px 12px;
        }
        /* Hover-to-expand sidebar (no media query needed - mobile hides sidebar via parent CSS) */
        .rb-sidebar:hover { width: 240px !important; align-items: flex-start !important; padding: 16px 12px !important; }
        .rb-sidebar:hover .rb-sidebar-item { justify-content: flex-start !important; }
        .rb-sidebar:hover .rb-sidebar-label { opacity: 1 !important; width: auto !important; }
        .rb-sidebar-item {
          width: 100%; display: flex; align-items: center;
          justify-content: center; padding: 12px; border-radius: 12px;
          color: #1E293B; cursor: pointer; transition: all 0.2s;
          margin-bottom: 8px; gap: 12px; border: none; background: transparent;
          min-height: 48px; white-space: nowrap; box-sizing: border-box;
          font-family: 'Inter', sans-serif;
        }
        .rb-sidebar.expanded .rb-sidebar-item { justify-content: flex-start; }
        .rb-sidebar-item:hover { background: #F8F5EF; color: #A47148; }
        .rb-sidebar-item.active { background: #F8F5EF; color: #A47148; font-weight: 700; }
        .rb-sidebar-icon { font-size: 1.3rem; min-width: 24px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
        .rb-sidebar-label {
          font-size: 0.9rem; font-weight: 600;
          opacity: 0; width: 0; overflow: hidden;
          transition: opacity 0.2s, width 0.2s;
          white-space: nowrap;
        }
        .rb-sidebar.expanded .rb-sidebar-label { opacity: 1; width: auto; }

        .rb-overlay {
          display: none; position: fixed; inset: 0;
          background: rgba(0,0,0,0.3); z-index: 998; cursor: pointer;
        }
        .rb-overlay.visible { display: block; }

        /* Mobile & Tablet Drawer Overrides */
        @media (max-width: 767px) {
          .rb-main-header {
            height: 64px !important;
            padding: 0 16px !important;
          }
          .rb-header-left {
            display: contents;
          }
          .rb-logo {
            position: absolute !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
          }
          .rb-hamburger {
            order: -1 !important;
            margin-right: auto !important;
          }
          .rb-header-right {
            margin-left: auto !important;
            gap: 12px !important;
          }
          .rb-sidebar {
            top: 0 !important;
            bottom: 0 !important;
            width: 240px !important;
            transform: translateX(-100%);
            transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: 1005;
            box-shadow: 4px 0 24px rgba(0,0,0,0.15);
          }
          .rb-sidebar.expanded {
            transform: translateX(0) !important;
            width: 240px !important;
            align-items: flex-start !important;
            padding: 16px 12px !important;
          }
          .rb-sidebar.expanded .rb-sidebar-item { justify-content: flex-start !important; }
          .rb-sidebar.expanded .rb-sidebar-label { opacity: 1 !important; width: auto !important; }
        }
        @media (min-width: 768px) and (max-width: 1199px) {
          .rb-sidebar { transform: translateX(-100%); transition: transform 0.25s cubic-bezier(0.4,0,0.2,1); }
          .rb-sidebar.expanded { transform: translateX(0); width: 240px; }
        </style>
        """,
        unsafe_allow_html=True
    )
        
    render_navbar()
    render_sidebar()
        
    st.markdown(
        """

        <script>
        (function() {
          var COLLAPSED = '64px';
          var EXPANDED  = '240px';

          function getViewportWidth() {
            try { return window.parent.innerWidth || window.innerWidth; }
            catch(e) { return window.innerWidth; }
          }
          function isDesktop()  { return getViewportWidth() >= 1200; }
          function isTablet()   { return getViewportWidth() >= 768 && getViewportWidth() < 1200; }

          function syncParentPadding(w) {
            try {
              window.parent.document.documentElement.style.setProperty('--sidebar-w', w);
            } catch(e) {}
          }

          var sidebar = document.getElementById('rb-sidebar');
          var overlay = document.getElementById('rb-overlay');
          var hamburger = document.getElementById('rb-hamburger');

          if (sidebar) {
            sidebar.addEventListener('mouseenter', function() {
              if (isDesktop()) {
                sidebar.classList.add('expanded');
                syncParentPadding(EXPANDED);
              }
            });
            sidebar.addEventListener('mouseleave', function() {
              if (isDesktop()) {
                sidebar.classList.remove('expanded');
                syncParentPadding(COLLAPSED);
              }
            });
          }

          if (hamburger) {
            hamburger.addEventListener('click', function() {
              if (!isDesktop()) {
                sidebar.classList.toggle('expanded');
                if (overlay) {
                  overlay.classList.toggle('active', sidebar.classList.contains('expanded'));
                }
              } else {
                var isExpanded = sidebar.classList.contains('expanded');
                sidebar.classList.toggle('expanded');
                syncParentPadding(isExpanded ? COLLAPSED : EXPANDED);
              }
            });
          }

          if (overlay) {
            overlay.addEventListener('click', function() {
              sidebar.classList.remove('expanded');
              overlay.classList.remove('active');
            });
          }
        })();
        </script>
        """,
        unsafe_allow_html=True
    )

    resumes = list_resumes()
    
    # Sync search query states
    search_query = st.session_state.get("search_query_state", "")
    if "search_resumes_val" in st.session_state and st.session_state.search_resumes_val != search_query:
        st.session_state.search_query_state = st.session_state.search_resumes_val
        search_query = st.session_state.search_resumes_val
    elif "mob_search_resumes_val" in st.session_state and st.session_state.mob_search_resumes_val != search_query:
        st.session_state.search_query_state = st.session_state.mob_search_resumes_val
        search_query = st.session_state.mob_search_resumes_val
    
    render_hero()

    # 4. Search & Filter Section (Desktop)
    render_search_bar_desktop(search_query)

    # 4. Search & Filter Section (Mobile)
    render_search_bar_mobile(search_query)
    
    # Filter matching resumes (shared logic)
    if search_query:
        search_query_clean = search_query.strip().lower()
        resumes = [r for r in resumes if search_query_clean in r["title"].lower() or search_query_clean in r["template"].lower()]

    # 5. Continue Editing (Desktop)
    if resumes:
        latest = resumes[0]
        rel_time = format_relative_time(latest["last_edited"])
        
        st.markdown('<div class="section-header-row"><span class="section-title">Continue Editing</span></div>', unsafe_allow_html=True)
        st.markdown('<div id="continue-card-marker"></div>', unsafe_allow_html=True)
        
        c_col1, c_col2 = st.columns([4.2, 0.8])
        with c_col1:
            render_continue_card_desktop(latest, tpl_disp, rel_time)
        with c_col2:
            st.markdown('<div class="continue-edit-btn-wrapper">', unsafe_allow_html=True)
            if st.button("&#9999;&#65039;", key="btn_continue_icon", use_container_width=True):
                load_active_resume(latest["path"])
                st.session_state.navigation_page = "workspace"
                st.session_state.editor_step = 0
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # 5. Continue Editing (Mobile)
    if resumes:
        latest = resumes[0]
        rel_time = format_relative_time(latest["last_edited"])
        tpl_disp = ALL_TEMPLATES.get(latest["template"], {}).get("name", latest["template"])
        
        st.markdown('<div class="mob-section-header-row mob-continue-section-marker"><span class="mob-section-title">Continue Editing</span></div>', unsafe_allow_html=True)
        render_continue_card_mobile(latest, tpl_disp, rel_time)
        if st.button("&#9999;&#65039;", key="mob_btn_continue_icon", use_container_width=True):
            load_active_resume(latest["path"])
            st.session_state.navigation_page = "workspace"
            st.session_state.editor_step = 0
            st.rerun()

    # 6. My Resumes Grid Section (Desktop)
    st.markdown('<div class="section-header-row resumes-section-marker"><span class="section-title">My Resumes</span></div>', unsafe_allow_html=True)
    
    if not resumes:
        st.info("No resumes found.")
        with st.container():
            st.markdown('<div id="my-resumes-grid-marker"></div>', unsafe_allow_html=True)
            st.markdown(
                """
                <div class="dashed-create-card" id="btn-dashed-create-card-trigger">
                    <div class="dashed-create-icon">&#x2795;</div>
                    <div class="dashed-create-text">Create New Resume</div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        with st.container():
            st.markdown('<div id="my-resumes-grid-marker"></div>', unsafe_allow_html=True)
            for idx, r in enumerate(resumes):
                tpl_disp = ALL_TEMPLATES.get(r["template"], {}).get("name", r["template"])
                rel_time = format_relative_time(r["last_edited"])
                
                with st.container():
                    render_resume_grid_card(r, tpl_disp, rel_time)
                    
                    act_col1, act_col2, act_col3 = st.columns([1.2, 1.2, 0.8])
                    with act_col1:
                        if st.button("Edit", key=f"grid_edit_{idx}", use_container_width=True):
                            load_active_resume(r["path"])
                            st.session_state.navigation_page = "workspace"
                            st.session_state.editor_step = 0
                            st.rerun()
                    with act_col2:
                        pdf_file_path = r["path"].replace(".json", ".pdf")
                        if os.path.exists(pdf_file_path):
                            with open(pdf_file_path, "rb") as pf:
                                pdf_data = pf.read()
                            safe_title = re.sub(r"[^a-zA-Z0-9]", "_", r["title"])
                            st.download_button(
                                "PDF",
                                data=pdf_data,
                                file_name=f"{safe_title}_Resume.pdf",
                                mime="application/pdf",
                                key=f"grid_dl_pdf_{idx}",
                                use_container_width=True
                            )
                        else:
                            st.button("PDF", key=f"grid_dl_pdf_disabled_{idx}", disabled=True, use_container_width=True)
                    with act_col3:
                        with st.popover("⋮", key=f"grid_options_{idx}", use_container_width=True):
                            # Rename input
                            new_title = st.text_input("Rename:", value=r["title"], key=f"rename_input_{idx}")
                            if new_title.strip() != r["title"]:
                                with open(r["path"], "r", encoding="utf-8") as f:
                                    content = json.load(f)
                                content.setdefault("metadata", {})["title"] = new_title.strip()
                                content["metadata"]["last_edited"] = time.time()
                                with open(r["path"], "w", encoding="utf-8") as f:
                                    json.dump(content, f, indent=2)
                                st.rerun()
                                
                            # Duplicate option
                            if st.button("&#128101; Duplicate", key=f"btn_dup_pop_{idx}", use_container_width=True):
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
                                
                            # Delete option
                            is_root = (os.path.abspath(r["path"]) == os.path.abspath(os.path.join(PROJECT_ROOT, "resume.json")))
                            if st.button("&#x1F5D1;&#65039; Delete", key=f"btn_del_pop_{idx}", use_container_width=True, disabled=is_root):
                                if os.path.exists(r["path"]):
                                    os.remove(r["path"])
                                if os.path.exists(pdf_file_path):
                                    os.remove(pdf_file_path)
                                st.rerun()
            
            # Dashed Create Card appended at the end of loop
            st.markdown(
                """
                <div class="dashed-create-card" id="btn-dashed-create-card-trigger">
                    <div class="dashed-create-icon">&#x2795;</div>
                    <div class="dashed-create-text">Create New Resume</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # 6. My Resumes Section (Mobile)
    st.markdown('<div class="mob-section-header-row mob-resumes-section-marker"><span class="mob-section-title">My Resumes</span></div>', unsafe_allow_html=True)
    
    if not resumes:
        st.markdown(
            """
            <div class="mob-dashed-create-card" id="mob-btn-dashed-create-card-trigger">
                <div class="mob-dashed-create-icon">&#x2795;</div>
                <div class="mob-dashed-create-text">Create New Resume</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        for idx, r in enumerate(resumes):
            tpl_disp = ALL_TEMPLATES.get(r["template"], {}).get("name", r["template"])
            rel_time = format_relative_time(r["last_edited"])
            
            st.markdown(
                f"""
                <div class="mob-resume-card-container">
                    <div class="mob-resume-card-left">
                        <div class="mob-resume-card-thumb">&#x1F4C4;</div>
                        <div class="mob-resume-card-info">
                            <div class="mob-resume-card-title">{html.escape(r["title"])}</div>
                            <div class="mob-resume-card-meta">
                                <span class="mob-resume-card-badge">{tpl_disp}</span>
                                <span class="mob-resume-card-time">Updated {rel_time}</span>
                            </div>
                        </div>
                    </div>
                    <div class="mob-resume-card-right-placeholder"></div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            mob_act_col1, mob_act_col2 = st.columns([3, 1])
            with mob_act_col1:
                if st.button("Edit", key=f"mob_grid_edit_{idx}", use_container_width=True):
                    load_active_resume(r["path"])
                    st.session_state.navigation_page = "workspace"
                    st.session_state.editor_step = 0
                    st.rerun()
            with mob_act_col2:
                with st.popover("⋮", key=f"mob_grid_options_{idx}", use_container_width=True):
                    new_title = st.text_input("Rename:", value=r["title"], key=f"mob_rename_input_{idx}")
                    if new_title.strip() != r["title"]:
                        with open(r["path"], "r", encoding="utf-8") as f:
                            content = json.load(f)
                        content.setdefault("metadata", {})["title"] = new_title.strip()
                        content["metadata"]["last_edited"] = time.time()
                        with open(r["path"], "w", encoding="utf-8") as f:
                            json.dump(content, f, indent=2)
                        st.rerun()
                        
                    if st.button("&#128101; Duplicate", key=f"mob_btn_dup_pop_{idx}", use_container_width=True):
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
                        
                    is_root = (os.path.abspath(r["path"]) == os.path.abspath(os.path.join(PROJECT_ROOT, "resume.json")))
                    if st.button("&#x1F5D1;&#65039; Delete", key=f"mob_btn_del_pop_{idx}", use_container_width=True, disabled=is_root):
                        if os.path.exists(r["path"]):
                            os.remove(r["path"])
                        pdf_file_path = r["path"].replace(".json", ".pdf")
                        if os.path.exists(pdf_file_path):
                            os.remove(pdf_file_path)
                        st.rerun()
        
        st.markdown(
            """
            <div class="mob-dashed-create-card" id="mob-btn-dashed-create-card-trigger">
                <div class="mob-dashed-create-icon">&#x2795;</div>
                <div class="mob-dashed-create-text">Create New Resume</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 7. Popular Templates Section (Canva scrollable row)
    st.markdown('<div class="section-header-row template-section-marker"><span class="section-title">Popular Templates</span></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="template-scroll-container">
          <div class="template-scroll-card" id="tpl-ats">
            <div class="template-scroll-thumb">&#x1F4BC;</div>
            <div class="template-scroll-name">ATS</div>
          </div>
          <div class="template-scroll-card" id="tpl-modern">
            <div class="template-scroll-thumb">&#x1F3A8;</div>
            <div class="template-scroll-name">Modern</div>
          </div>
          <div class="template-scroll-card" id="tpl-minimal">
            <div class="template-scroll-thumb">&#x2728;</div>
            <div class="template-scroll-name">Minimal</div>
          </div>
          <div class="template-scroll-card" id="tpl-creative">
            <div class="template-scroll-thumb">&#x1F680;</div>
            <div class="template-scroll-name">Creative</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Bottom Navigation Bar Sticky using marker and columns (hidden on desktop, active on mobile)
    render_bottom_nav()

    # Render wizard dialog if active
    if st.session_state.get("show_create_dialog", False):
        show_create_resume_dialog()

    # Hidden create button trigger mapping
    st.markdown('<div style="display:none;">', unsafe_allow_html=True)
    if st.button("", key="btn_dashed_create_arrow"):
        st.session_state.wizard_just_opened = True
        st.session_state.show_create_dialog = True
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # FAB (Mobile Only)
    st.markdown('<div class="mob-fab" id="mob-fab-trigger">＋</div>', unsafe_allow_html=True)



    # JavaScript navigation event mapping (Desktop sidebar & Mobile bottom nav)
    st.markdown(
        """
        <script>
        const parentDoc = window.parent.document;
        
        function setupNavigation() {
          const sbHome = parentDoc.getElementById('sb-home');
          if (sbHome && !sbHome.dataset.navSetup) {
            sbHome.dataset.navSetup = "true";
            sbHome.addEventListener('click', () => {
              parentDoc.querySelector('.main .block-container')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
          }
          
          const sbTemplates = parentDoc.getElementById('sb-templates');
          if (sbTemplates && !sbTemplates.dataset.navSetup) {
            sbTemplates.dataset.navSetup = "true";
            sbTemplates.addEventListener('click', () => {
              parentDoc.querySelector('.template-section-marker')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
          }
        
          const sbResumes = parentDoc.getElementById('sb-resumes');
          if (sbResumes && !sbResumes.dataset.navSetup) {
            sbResumes.dataset.navSetup = "true";
            sbResumes.addEventListener('click', () => {
              parentDoc.querySelector('.resumes-section-marker')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
          }
          
          const sbProfile = parentDoc.getElementById('sb-profile');
          if (sbProfile && !sbProfile.dataset.navSetup) {
            sbProfile.dataset.navSetup = "true";
            sbProfile.addEventListener('click', () => {
              const createBtn = parentDoc.querySelector('button[key="btn_dashed_create_arrow"]');
              if (createBtn) createBtn.click();
            });
          }
        
          const bottomNavButtons = parentDoc.querySelectorAll('div:has(#bottom-nav-marker) + div button');
          if (bottomNavButtons && bottomNavButtons.length >= 4) {
            if (!bottomNavButtons[0].dataset.navSetup) {
              bottomNavButtons[0].dataset.navSetup = "true";
              bottomNavButtons[0].addEventListener('click', (e) => {
                parentDoc.querySelector('.main .block-container')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
              });
            }
            if (!bottomNavButtons[1].dataset.navSetup) {
              bottomNavButtons[1].dataset.navSetup = "true";
              bottomNavButtons[1].addEventListener('click', (e) => {
                parentDoc.querySelector('.template-section-marker')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
              });
            }
            if (!bottomNavButtons[2].dataset.navSetup) {
              bottomNavButtons[2].dataset.navSetup = "true";
              bottomNavButtons[2].addEventListener('click', (e) => {
                parentDoc.querySelector('.resumes-section-marker')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
              });
            }
            if (!bottomNavButtons[3].dataset.navSetup) {
              bottomNavButtons[3].dataset.navSetup = "true";
              bottomNavButtons[3].addEventListener('click', (e) => {
                const createBtn = parentDoc.querySelector('button[key="btn_dashed_create_arrow"]');
                if (createBtn) createBtn.click();
              });
            }
          }
        
          ['tpl-ats', 'tpl-modern', 'tpl-minimal', 'tpl-creative'].forEach(id => {
            const card = parentDoc.getElementById(id);
            if (card && !card.dataset.navSetup) {
              card.dataset.navSetup = "true";
              card.addEventListener('click', () => {
                const btn = parentDoc.querySelector('button[key="btn_dashed_create_arrow"]');
                if (btn) btn.click();
              });
            }
          });
          
          const dashedCreate = parentDoc.getElementById('btn-dashed-create-card-trigger');
          if (dashedCreate && !dashedCreate.dataset.clickSetup) {
            dashedCreate.dataset.clickSetup = "true";
            dashedCreate.addEventListener('click', () => {
              const createBtn = parentDoc.querySelector('button[key="btn_dashed_create_arrow"]');
              if (createBtn) createBtn.click();
            });
          }

          // Mobile FAB setup
          const mobFab = parentDoc.getElementById('mob-fab-trigger');
          if (mobFab && !mobFab.dataset.clickSetup) {
            mobFab.dataset.clickSetup = "true";
            mobFab.addEventListener('click', () => {
              const createBtn = parentDoc.querySelector('button[key="btn_dashed_create_arrow"]');
              if (createBtn) createBtn.click();
            });
          }

          // Mobile Dashed Create Card triggers
          const mobDashedCreates = parentDoc.querySelectorAll('.mob-dashed-create-card');
          mobDashedCreates.forEach(el => {
            if (el && !el.dataset.clickSetup) {
              el.dataset.clickSetup = "true";
              el.addEventListener('click', () => {
                const createBtn = parentDoc.querySelector('button[key="btn_dashed_create_arrow"]');
                if (createBtn) createBtn.click();
              });
            }
          });

          // Mobile Bottom Nav items setup
          const mobNavHome = parentDoc.getElementById('mob-nav-home');
          if (mobNavHome && !mobNavHome.dataset.clickSetup) {
            mobNavHome.dataset.clickSetup = "true";
            mobNavHome.addEventListener('click', () => {
              parentDoc.querySelector('.main .block-container')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
              setActiveMobTab('mob-nav-home');
            });
          }

          const mobNavTemplates = parentDoc.getElementById('mob-nav-templates');
          if (mobNavTemplates && !mobNavTemplates.dataset.clickSetup) {
            mobNavTemplates.dataset.clickSetup = "true";
            mobNavTemplates.addEventListener('click', () => {
              const createBtn = parentDoc.querySelector('button[key="btn_dashed_create_arrow"]');
              if (createBtn) createBtn.click();
              setActiveMobTab('mob-nav-templates');
            });
          }

          const mobNavResumes = parentDoc.getElementById('mob-nav-resumes');
          if (mobNavResumes && !mobNavResumes.dataset.clickSetup) {
            mobNavResumes.dataset.clickSetup = "true";
            mobNavResumes.addEventListener('click', () => {
              parentDoc.querySelector('.mob-resumes-section-marker')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
              setActiveMobTab('mob-nav-resumes');
            });
          }

          const mobNavProfile = parentDoc.getElementById('mob-nav-profile');
          if (mobNavProfile && !mobNavProfile.dataset.clickSetup) {
            mobNavProfile.dataset.clickSetup = "true";
            mobNavProfile.addEventListener('click', () => {
              const createBtn = parentDoc.querySelector('button[key="btn_dashed_create_arrow"]');
              if (createBtn) createBtn.click();
              setActiveMobTab('mob-nav-profile');
            });
          }

          function setActiveMobTab(id) {
            ['mob-nav-home', 'mob-nav-templates', 'mob-nav-resumes', 'mob-nav-profile'].forEach(tid => {
              const el = parentDoc.getElementById(tid);
              if (el) {
                el.classList.toggle('active', tid === id);
              }
            });
          }
        }
        
        setupNavigation();
        const observer = new MutationObserver(setupNavigation);
        observer.observe(parentDoc.body, { childList: true, subtree: true });
        </script>
        """,
        unsafe_allow_html=True
    )




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
        f'    <span class="repo-chip">&#x2B50; {repo.get("stars", 0)}</span>'
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
    ("&#x1F464;", "Personal"),
    ("&#x1F393;", "Education"),
    ("&#x1F4BC;", "Experience"),
    ("&#x1F680;", "Projects"),
    ("&#x1F6E0;&#65039;", "Skills"),
    ("&#x2705;", "Review"),
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
                    if st.button("&#x2795; Add Education", key="add_edu", use_container_width=True):
                        push_undo(d)
                        d.setdefault("education",[]).append(
                            {"degree":"","institution":"","details":"","period":""})
                        save_to_disk(d); st.session_state.resume = d; st.rerun()
                with ec2:
                    if d.get("education") and st.button("&#x1F5D1; Remove Last", key="rm_edu", use_container_width=True):
                        push_undo(d)
                        d["education"].pop()
                        save_to_disk(d); st.session_state.resume = d; st.rerun()

                if not d.get("education"):
                    st.info("No education added yet.")
                for i, edu in enumerate(d.get("education",[])):
                    dg = edu.get("degree","") or "Degree"
                    sc = edu.get("institution","") or "Institution"
                    with st.expander(f"&#x1F393; {dg} — {sc}", expanded=(i==0)):
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
                    if st.button("&#x2795; Add Position", key="add_por", use_container_width=True):
                        push_undo(d)
                        d.setdefault("position_of_responsibility",[]).append(
                            {"role":"","period":"","bullets":[]})
                        save_to_disk(d); st.session_state.resume = d; st.rerun()
                with pr2:
                    if d.get("position_of_responsibility") and st.button("&#x1F5D1; Remove Last", key="rm_por", use_container_width=True):
                        push_undo(d)
                        d["position_of_responsibility"].pop()
                        save_to_disk(d); st.session_state.resume = d; st.rerun()
                for i, por in enumerate(d.get("position_of_responsibility",[])):
                    role = por.get("role","") or "Position"
                    with st.expander(f"&#x1F91D; {role}", expanded=(i==0)):
                        r1, r2 = st.columns([.7,.3])
                        with r1: st.text_input("Role & Organisation", por.get("role",""),   key=f"f_prr{i}")
                        with r2: st.text_input("Period",              por.get("period",""), key=f"f_prp{i}")
                        st.text_area("Bullets", "\n".join(por.get("bullets",[])),
                                     height=72, key=f"f_prb{i}")

            elif current_step == 2:
                st.markdown('<div class="sec-title">Work Experience</div>', unsafe_allow_html=True)
                ec1, ec2 = st.columns(2)
                with ec1:
                    if st.button("&#x2795; Add Job", key="add_exp", use_container_width=True):
                        push_undo(d)
                        d.setdefault("experience",[]).append(
                            {"role":"","company":"","location":"","period":"","technologies":"","bullets":[]})
                        save_to_disk(d); st.session_state.resume = d; st.session_state.last_hash = ""; st.rerun()
                with ec2:
                    if d.get("experience") and st.button("&#x1F5D1; Remove Last", key="rm_exp", use_container_width=True):
                        push_undo(d)
                        d["experience"].pop()
                        save_to_disk(d); st.session_state.resume = d; st.session_state.last_hash = ""; st.rerun()

                if not d.get("experience"):
                    st.info("No experience added yet. Click **&#x2795; Add Job** above.")
                for i, exp in enumerate(d.get("experience",[])):
                    title   = exp.get("role","") or "New Role"
                    company = exp.get("company","") or "Company"
                    with st.expander(f"&#x1F4BC; {title} @ {company}", expanded=(i==0)):
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
                                    f'<div style="font-weight:700; color:#B45309; font-size:0.85rem;">&#x1F4A1; Make This Stronger</div>'
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
                    if st.button("&#x2795; Add Project", key="add_proj", use_container_width=True):
                        push_undo(d)
                        d.setdefault("projects",[]).append(
                            {"title":"","link":"","date":"","tools":"","bullets":[]})
                        save_to_disk(d); st.session_state.resume = d; st.session_state.last_hash = ""; st.rerun()
                with pc2:
                    if d.get("projects") and st.button("&#x1F5D1; Remove Last", key="rm_proj", use_container_width=True):
                        push_undo(d)
                        d["projects"].pop()
                        save_to_disk(d); st.session_state.resume = d; st.session_state.last_hash = ""; st.rerun()

                # Inline GitHub Import (Phase 3)
                with st.expander("&#x1F419; Import from GitHub", expanded=True):
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
                                                st.success(f"&#x2705; Added {repo['name']} to your resume")

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
                                                st.success(f"&#x2705; Added {repo['name']} to your resume")

                        else:
                            st.warning("No public repositories found.")

                if not d.get("projects"):
                    st.info("No projects added yet. Click **&#x2795; Add Project** above.")
                for i, pr in enumerate(d.get("projects",[])):
                    title = pr.get("title","") or "New Project"
                    with st.expander(f"&#x1F680; {title}", expanded=(i==0)):
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
                                    f'<div style="font-weight:700; color:#B45309; font-size:0.85rem;">&#x1F4A1; Make This Stronger</div>'
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
                        if st.button("&#x1F5D1;", key=f"rm_sk{i}", help="Remove this skill category"):
                            push_undo(d)
                            new_sk_after_del = {kk: vv for j,(kk,vv) in enumerate(sk.items()) if j != i}
                            d["technical_skills"] = new_sk_after_del
                            save_to_disk(d); st.session_state.resume = d; st.session_state.last_hash = ""; st.rerun()
                    if nk:
                        new_sk[nk] = nv

                st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
                st.markdown("**&#x2795; Add new skill category:**")
                nc1, nc2, nc3 = st.columns([.30, .60, .10])
                with nc1: st.text_input("New Category", "", placeholder="e.g. Databases", key="f_ncat")
                with nc2: st.text_input("Skills",       "", placeholder="e.g. MySQL, MongoDB", key="f_nval")
                with nc3:
                    st.markdown('<div style="margin-top:28px"></div>', unsafe_allow_html=True)
                    if st.button("&#x2795;", key="add_sk_btn", help="Add this skill category"):
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
                    st.markdown("##### &#x1F4A1; Recommended Skills to Add")
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
                        st.success(f"&#x2705; Added {', '.join(selected_missing)} to {first_cat}!")
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
                    "sejal_original": {"name": "Modern Accent", "desc": "Clean typography with subtle color accents.", "icon": "&#x1F3A8;", "color": "#6366F1"},
                    "ats":            {"name": "ATS Professional", "desc": "Industry-standard, highly scannable layout.", "icon": "&#x1F4BC;", "color": "#1E293B"},
                    "modern":         {"name": "Elegant Modern", "desc": "Stylish sans-serif theme with modern headings.", "icon": "&#x2728;", "color": "#0F766E"},
                    "creative":       {"name": "Creative Bold", "desc": "Vibrant design to stand out in creative roles.", "icon": "&#x1F680;", "color": "#E11D48"},
                    "minimal":        {"name": "Minimalist Clean", "desc": "Simple, elegant spacing focusing on content.", "icon": "&#x1F4C4;", "color": "#475569"},
                    "two_column":     {"name": "Two Column Splitted", "desc": "Balanced two-column split layout.", "icon": "&#x1F4CA;", "color": "#7C3AED"}
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
                            st.download_button("&#x1F4E5; Download index.html", data=hc.encode(),
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
                    f'<span style="font-weight:700; color:#065F46; font-size:0.88rem;">&#x2705; {step_title} Section Completed</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                if _tips:
                    with st.expander("&#x1F4A1; Tips to improve this section", expanded=False):
                        for tip in _tips:
                            st.markdown(f"- {tip}")
                
                improve_col, quality_col = st.columns(2)
                with quality_col:
                    if st.button("&#x1F4CA; Check Resume Quality", key="step_check_quality_btn", use_container_width=True):
                        st.session_state.workspace_tab = "Insights"
                        st.rerun()

            # --- PREVIOUS / NEXT STEP BUTTONS ---
            st.markdown('<div class="hdiv"></div>', unsafe_allow_html=True)
            btn_l, btn_r = st.columns([1, 1])
            with btn_l:
                prev_disabled = (current_step == 0)
                if st.button("&#x2190; Previous", key="wz_prev_btn", disabled=prev_disabled, use_container_width=True):
                    st.session_state.editor_step = current_step - 1
                    st.rerun()
            with btn_r:
                if current_step < len(WIZARD_STEPS) - 1:
                    next_label = WIZARD_STEPS[current_step + 1][1]
                    if st.button(f"Next: {next_label} &#x2192;", key="wz_next_btn", use_container_width=True, type="primary"):
                        st.session_state.editor_step = current_step + 1
                        st.rerun()
                else:
                    if st.button("&#x1F3E0; Go Home", key="wz_finish_btn", use_container_width=True, type="primary"):
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

        # &#x1F916; Resume Coach Card
        st.markdown(
            f'<div style="background: #FFFFFF; border: 1.5px solid {"#E2E8F0" if score >= 80 else "#FEF3C7"}; '
            f'border-radius: 12px; padding: 16px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">'
            f'<div style="display: flex; align-items: center; gap: 8px;">'
            f'<span style="font-size: 1.3rem;">&#x1F916;</span>'
            f'<span style="font-weight: 800; font-size: 1.05rem; color: #1E293B;">Resume Coach</span>'
            f'</div>'
            f'<div style="margin-top: 8px; font-size: 0.85rem; color: #64748B;">'
            f'Resume Health Score: <strong style="color: {"#10B981" if score >= 80 else "#D97706"}; font-size: 1.1rem;">{score}%</strong>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        if score < 80:
            st.markdown("##### &#x26A0;&#65039; Suggestions to improve:")
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
                f'<span style="font-weight:700; color:#065F46; font-size:0.9rem;">&#x1F389; Resume {score}% Complete!</span><br/>'
                f'<span style="color:#047857; font-size:0.78rem;">You have unlocked the Career Assistant tools.</span>'
                f'</div>',
                unsafe_allow_html=True
            )
            
            st.markdown("##### &#x1F4CB; Recommended Final Checks")
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
            
            st.markdown("##### &#x1F680; Guided Career Assistant")
            gc_col1, gc_col2 = st.columns(2)
            with gc_col1:
                if st.button("&#x1F680; Improve Resume", key="ca_improve_res", use_container_width=True):
                    st.session_state.workspace_tab = "Insights"
                    st.session_state.career_active_tool = "consistency"
                    st.rerun()
                if st.button("&#x1F4C8; Analyze Skill Gaps", key="ca_skill_gaps", use_container_width=True):
                    st.session_state.workspace_tab = "Insights"
                    st.session_state.career_active_tool = "gap_analyzer"
                    st.rerun()
            with gc_col2:
                if st.button("&#x1F4BC; Prep Interviews", key="ca_prep_int", use_container_width=True):
                    st.session_state.workspace_tab = "Insights"
                    st.session_state.career_active_tool = "interview_prep"
                    st.rerun()
                if st.button("&#x1F419; Verify GitHub Evidence", key="ca_github_ev", use_container_width=True):
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
                if st.button("&#x1F4BB;", key="btn_view_desk", type="primary" if is_desk else "secondary", help="Desktop view"):
                    st.session_state.device_view = "desktop"
                    st.rerun()
            with lh_sub3:
                is_mob = (st.session_state.get("device_view", "desktop") == "mobile")
                if st.button("&#x1F4F1;", key="btn_view_mob", type="primary" if is_mob else "secondary", help="Mobile view"):
                    st.session_state.device_view = "mobile"
                    st.rerun()

        with st.spinner("&#x1F504; Updating preview…"):
            try:
                maybe_compile(d, TID, C, M, FS, FT)
            except Exception as compile_err:
                st.session_state.cok = False
                st.session_state.cmsg = f"Compilation error: {compile_err}"

        if st.session_state.cmsg:
            st.warning(f"&#x26A0;&#65039; {st.session_state.cmsg}")

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

  pdfjsLib.getDocument({{
    data: b64ToArr(base64PDF),
    standardFontDataUrl: 'https://cdn.jsdelivr.net/npm/pdfjs-dist@3.4.120/standard_fonts/'
  }}).promise.then(async (pdf) => {{
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
        with st.expander("&#x1F4A1; Improvement Tips", expanded=False):
            for s in hs["suggestions"][:5]:
                st.markdown(f"- {s}")
else:
    st.markdown("""
    <div class="preview-card" style="display:flex;flex-direction:column;
      align-items:center;justify-content:center;min-height:480px;gap:12px;">
      <div style="font-size:3.5rem;">&#x1F4C4;</div>
      <div style="font-size:.95rem;color:#64748B;font-weight:500;text-align:center;">
        Your live resume preview will appear here.<br>
        <span style="font-size:.8rem;color:#94A3B8;">
        Edits on the left update automatically.</span>
      </div>
    </div>""", unsafe_allow_html=True)
    if st.session_state.cmsg:
        st.error(f"&#x274C; {st.session_state.cmsg}")

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
        with st.popover("&#x2728; More Actions", use_container_width=True):
            st.markdown("### Resume Utilities")
            if st.button("&#x1F4E5; Import Resume", key="fbar_import", use_container_width=True):
                st.session_state.show_import = True
                st.rerun()
            if st.button("&#x1F4CA; Open Insights", key="fbar_open_ins", use_container_width=True):
                st.session_state.workspace_tab = "Insights"
                st.session_state.navigation_page = "workspace"
                st.rerun()
            if st.button("&#x1F4E5; Demo Resume", key="fbar_demo", use_container_width=True):
                st.session_state.resume = copy.deepcopy(DEMO_RESUME)
                st.session_state.last_hash = ""
                save_to_disk(st.session_state.resume)
                st.rerun()
            if st.button("&#x1F504; Reset Form", key="fbar_reset", use_container_width=True):
                st.session_state.resume = copy.deepcopy(DEFAULT)
                st.session_state.last_hash = ""
                save_to_disk(st.session_state.resume)
                st.rerun()
            
    with bf_dl:
        pname = d.get("personal",{}).get("name","Resume")
        safe_name = re.sub(r"[^a-zA-Z0-9]","_",pname).strip("_") or "Resume"
        if st.session_state.pdf_raw:
            st.download_button(
                "&#x1F4E5; Download PDF",
                data=st.session_state.pdf_raw,
                file_name=f"{safe_name}_Resume.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary",
                key="fbar_dl_pdf"
            )
        else:
            st.button("&#x1F4E5; Download PDF", key="fbar_dl_pdf_disabled", disabled=True, use_container_width=True)
