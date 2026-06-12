import streamlit as st
import json
import os
import time
import copy
import base64

from core.pdf_engine import build_pdf
from resume_builder.utils.validators import resume_hash

# Compute PROJECT_ROOT dynamically relative to this file
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RESUME_BUILDER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FITTING_OPTS = ["Auto Compress", "Keep Original", "Multi-Page"]

@st.cache_data(ttl=60, show_spinner=False)
def _read_json(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return copy.deepcopy(st.session_state.get("DEFAULT_RESUME", {}))

def get_pdf_path_for_json(json_path: str) -> str:
    base = os.path.basename(json_path)
    pdf_name = os.path.splitext(base)[0] + ".pdf"
    pdf_dir = os.path.join(PROJECT_ROOT, "exports", "pdf")
    os.makedirs(pdf_dir, exist_ok=True)
    return os.path.join(pdf_dir, pdf_name)

def get_profile_path() -> str:
    if "current_profile_path" not in st.session_state:
        target_dir = os.path.join(PROJECT_ROOT, "exports", "json")
        os.makedirs(target_dir, exist_ok=True)
        st.session_state.current_profile_path = os.path.join(target_dir, "resume.json")
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
        pdf_path = get_pdf_path_for_json(get_profile_path())
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
        resume = copy.deepcopy(st.session_state.get("DEFAULT_RESUME", {}))
        
    if "metadata" not in resume:
        resume["metadata"] = {}
    meta = resume["metadata"]
    
    # Ensure title is present
    if not meta.get("title"):
        if os.path.abspath(path) == os.path.abspath(os.path.join(PROJECT_ROOT, "exports", "json", "resume.json")):
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
    pdf_path = get_pdf_path_for_json(path)
    if not os.path.exists(pdf_path):
        try:
            from resume_builder.generators.pdf_generator import build_pdf as local_build_pdf
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            local_build_pdf(
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
    versions_dir = os.path.join(PROJECT_ROOT, "exports", "json")
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
                    if fname == "resume.json":
                        title = meta.get("title") or "Default Resume"
                    else:
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

def save_checkpoint(path: str, data: dict):
    """Save a resume version snapshot to the history directory."""
    if not path or not os.path.exists(path):
        return
    base_name = os.path.splitext(os.path.basename(path))[0]
    history_dir = os.path.join(PROJECT_ROOT, "exports", "json", "history", base_name)
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


def maybe_compile(d: dict, template_id: str, C: str, M: int, FS: float, FT: str):
    """Compile PDF only when content hash changed."""
    h = resume_hash(d, C, M, FS, template_id, FT)
    if h == st.session_state.last_hash and st.session_state.pdf_b64:
        return   # nothing changed
    st.session_state.last_hash = h
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    ctx = get_script_run_ctx()
    session_id = ctx.session_id if ctx else "default"
    pdf_out = os.path.join(PROJECT_ROOT, "exports", "pdf", f"live_{session_id}.pdf")
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
        with open(pdf_out, "rb") as pf: raw = pf.read()
        st.session_state.pdf_raw = raw
        st.session_state.pdf_b64 = base64.b64encode(raw).decode()

