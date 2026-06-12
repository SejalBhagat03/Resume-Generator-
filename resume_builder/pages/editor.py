import streamlit as st
import os
import json
import time
import re
import copy
import html
import base64
from resume_builder.utils.helpers import clean_html

# Import storage services
from resume_builder.services.storage import (
    save_to_disk,
    load_from_disk,
    load_active_resume,
    get_profile_path,
    save_checkpoint,
    load_local_pdfjs_assets,
    maybe_compile,
)

# Import helpers/validators
from resume_builder.utils.helpers import margin_label, fscale_label, format_relative_time
from resume_builder.utils.validators import sanitize_html

# Import analysis and career dashboard
from resume_builder.services.ai import calculate_health_score, AchievementQuantifier, CareerGapAnalyzer
from resume_builder.services.github import GitHubIntegration
from resume_builder.career_dashboard import show_career_center

# Import components
from resume_builder.components.navbar import render_navbar
from resume_builder.components.sidebar import render_sidebar
from resume_builder.components.dialogs import show_import_dialog
from resume_builder.components.wizard import show_create_resume_dialog
from resume_builder.components.bottom_nav import render_bottom_nav

# Import template registry
from resume_builder.templates import TEMPLATES as ALL_TEMPLATES

# Import pages components
from resume_builder.pages.templates import render_templates_gallery
from resume_builder.pages.settings import render_layout_settings

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MAX_HISTORY = 30
FITTING_OPTS = ["Auto Compress", "Keep Original", "Multi-Page"]

ACCENT_PRESETS = {
    "Brown": "#A86A3D", "Blue": "#2563EB", "Emerald": "#10B981",
    "Rose": "#E11D48", "Bronze": "#854D0E", "Slate": "#475569",
}

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

    # skills
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


def show_editor():
    """Phase 2: Live Editor Workspace rendering both Left form and Right Live PDF canvas."""
    
    # 1. Autosave changes immediately
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

    # Set default workspace tab if missing
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
                    new_path = os.path.join(PROJECT_ROOT, "exports", "json", f"{base_name}_copy.json")
                    counter = 1
                    while os.path.exists(new_path):
                        new_path = os.path.join(PROJECT_ROOT, "exports", "json", f"{base_name}_copy_{counter}.json")
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
                is_root = (os.path.abspath(get_profile_path()) == os.path.abspath(os.path.join(PROJECT_ROOT, "exports", "json", "resume.json")))
                if st.button("&#x1F5D1;&#65039; Delete", key="top_del_btn", use_container_width=True, disabled=is_root, help="Root resume cannot be deleted"):
                    if os.path.exists(get_profile_path()):
                        os.remove(get_profile_path())
                    st.session_state.current_profile_path = os.path.join(PROJECT_ROOT, "exports", "json", "resume.json")
                    st.session_state.resume = load_from_disk()
                    st.session_state.navigation_page = "home"
                    st.rerun()
            
    with c_saved:
        st.markdown('<div style="display: flex; align-items: center; justify-content: center; height: 38px;"><span style="color: #10B981; font-weight: 700; font-size: 0.85rem;">&#10003; Saved</span></div>', unsafe_allow_html=True)
        
    with c_history:
        base_name = os.path.splitext(os.path.basename(get_profile_path()))[0]
        history_dir = os.path.join(PROJECT_ROOT, "exports", "json", "history", base_name)
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
            st.rerun()
            
    with c_prev:
        is_active_prev = (st.session_state.workspace_tab == "Preview")
        if st.button("&#128065;&#65039; Preview", key="btn_wtab_prev", type="primary" if is_active_prev else "secondary", use_container_width=True):
            st.session_state.workspace_tab = "Preview"
            st.rerun()
            
    with c_ins:
        is_active_ins = (st.session_state.workspace_tab == "Insights")
        if st.button("&#x1F4CA; Insights", key="btn_wtab_ins", type="primary" if is_active_ins else "secondary", use_container_width=True):
            st.session_state.workspace_tab = "Insights"
            st.rerun()
            
    with c_accent:
        COLOR_ICONS = {
            "Brown": "&#128996; Brown",
            "Blue": "&#128309; Blue",
            "Emerald": "&#128994; Emerald",
            "Rose": "&#128308; Rose",
            "Bronze": "&#128999; Bronze",
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

    # ── SUB-HEADER PROGRESS CARD & TAB ROUTING ──
    comp_score, comp_status = calculate_completion_status(d)
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

    workspace_tab = st.session_state.get("workspace_tab", "Edit")

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
                try:
                    show_career_center()
                except Exception as e:
                    st.error(f"Career Center failed: {e}")
            else:  # Edit tab
                # Sub-header Stepper widget
                st.markdown('<div id="sub-header-marker"></div>', unsafe_allow_html=True)
                sc_meta, sc_s1, sc_s2, sc_s3, sc_s4, sc_s5, sc_s6 = st.columns(
                    [3.5, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6], gap="small"
                )
                with sc_meta:
                    st.markdown(
                        f'<div style="display: flex; flex-direction: column; justify-content: center; height: 55px; line-height: 1.25;">'
                        f'  <span style="font-size: 0.72rem; font-weight: 700; color: #A86A3D; text-transform: uppercase; letter-spacing: 0.05em;">Step {current_step + 1} of 6: {step_title}</span>'
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

                            # Inline Achievement Quantifier
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

                    # Inline GitHub Import
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

                            # Inline Achievement Quantifier
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

                    # Smart Skill Suggestions
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
                    render_templates_gallery(TID)

                    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
                    new_m, new_fs, new_ft = render_layout_settings(M, FS, FT)
                    
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
                                os.makedirs(os.path.join(PROJECT_ROOT, "exports", "html"), exist_ok=True)
                                hp = os.path.join(PROJECT_ROOT, "exports", "html", "index.html")
                                with open(hp,"w",encoding="utf-8") as hf: hf.write(hc)
                                st.download_button("&#x1F4E5; Download index.html", data=hc.encode(),
                                                   file_name="index.html", mime="text/html",
                                                   use_container_width=True, key="dl_port")
                    except Exception as ex:
                        st.error(f"Portfolio error: {ex}")

                # --- CONTEXT-AWARE COMPLETION BANNER ---
                step_is_done = _step_done(current_step, d)
                if step_is_done:
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
            st.markdown(
                clean_html(
                    """
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
                    """
                ),
                unsafe_allow_html=True
            )

            try:
                hs = calculate_health_score(d)
                score = hs["score"]

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
                        if st.button("ATS Check", key=f"fc_ats", use_container_width=True):
                            st.session_state.workspace_tab = "Insights"
                            st.session_state.career_active_tool = "consistency"
                            st.rerun()
                    with fc2:
                        if st.button("Consistency", key=f"fc_const", use_container_width=True):
                            st.session_state.workspace_tab = "Insights"
                            st.session_state.career_active_tool = "consistency"
                            st.rerun()
                    with fc3:
                        if st.button("Prep Interview", key=f"fc_prep", use_container_width=True):
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
            except Exception as e:
                st.error(f"Coach panel failed: {e}")

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

    const [x1, y1, x2, y2] = vp.convertToViewportRectangle(annot.rect);
    const left   = Math.min(x1, x2);
    const top    = Math.min(y1, y2);
    const width  = Math.abs(x2 - x1);
    const height = Math.abs(y2 - y1);

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

                if hs.get("suggestions"):
                    with st.expander("&#x1F4A1; Improvement Tips", expanded=False):
                        for s in hs["suggestions"][:5]:
                            st.markdown(f"- {s}")
    else:
        st.markdown(
            clean_html(
                """
                <div class="preview-card" style="display:flex;flex-direction:column;
                  align-items:center;justify-content:center;min-height:480px;gap:12px;">
                  <div style="font-size:3.5rem;">&#x1F4C4;</div>
                  <div style="font-size:.95rem;color:#64748B;font-weight:500;text-align:center;">
                    Your live resume preview will appear here.<br>
                    <span style="font-size:.8rem;color:#94A3B8;">
                    Edits on the left update automatically.</span>
                  </div>
                </div>
                """
            ),
            unsafe_allow_html=True
        )
        if st.session_state.cmsg:
            st.error(f"&#x274C; {st.session_state.cmsg}")

    # Keyboard shortcuts mapping script
    st.markdown(
        clean_html(
            """
            <script>
            const parentDoc = window.parent.document;
            parentDoc.addEventListener('keydown', function(e) {
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
            """
        ),
        unsafe_allow_html=True
    )

    # ── FIXED BOTTOM ACTIONS BAR ──
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
