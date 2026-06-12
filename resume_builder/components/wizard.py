import streamlit as st
import os
import re
import json
import copy
import time

from resume_builder.ui.wizard_ui import (
    render_wizard_header,
    render_wizard_stepper,
    render_profile_type_cards,
    render_import_cards,
)
from resume_builder.components.dialogs import render_pdf_thumbnail

@st.dialog("Create New Resume", width="large")
def show_create_resume_dialog():
    from resume_builder.templates import TEMPLATES
    from resume_builder.parser.reader import (
        extract_txt_text,
        extract_pdf_layout_and_text,
        extract_docx_layout_and_text,
    )
    from resume_builder.parser.engine import (
        segment_into_blocks,
        parse_mapped_blocks_to_json,
    )
    
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

    # Step progress indicator and UI rendering
    step = st.session_state.create_wizard_step
    # Header
    render_wizard_header()
    # Stepper
    render_wizard_stepper(step, ["Profile", "Import", "Theme"])

    # Step specific UI
    if step == 1:
        render_profile_type_cards(st.session_state.wizard_resume_type)
        
        st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
        w1_col1, w1_col2 = st.columns([1, 1])
        with w1_col1:
            if st.button("Cancel", use_container_width=True, key="wiz_cancel_1"):
                st.session_state.wizard_just_opened = True
                st.rerun()
        with w1_col2:
            if st.button("Next ➡️", type="primary", use_container_width=True, key="wiz_next_1"):
                st.session_state.create_wizard_step = 2
                st.rerun()

    elif step == 2:
        render_import_cards(st.session_state.wizard_import_source)
        
        if st.session_state.wizard_import_source == "GitHub":
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            st.markdown("**Enter GitHub Username to fetch projects:**")
            gh_user = st.text_input("GitHub Username", value=st.session_state.get("wizard_github_username", ""), placeholder="e.g. SejalBhagat03")
            if gh_user.strip():
                st.session_state.wizard_github_username = gh_user.strip()
                if st.button("🔍 Fetch Projects", type="primary", use_container_width=True):
                    with st.spinner("Fetching repositories..."):
                        from resume_builder.services.github import GitHubIntegration
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
                    
        elif st.session_state.wizard_import_source in ("Existing Resume", "LinkedIn PDF"):
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            st.markdown("**Upload your resume file (PDF, DOCX, TXT):**")
            uploaded_file = st.file_uploader("Upload resume file:", type=["pdf", "docx", "txt"], key="wizard_upload")
            if uploaded_file:
                st.session_state.wizard_uploaded_file = uploaded_file
                
        st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
        w2_col1, w2_col2 = st.columns(2)
        with w2_col1:
            if st.button("⬅️ Back", use_container_width=True, key="wiz_back_2"):
                st.session_state.create_wizard_step = 1
                st.rerun()
        with w2_col2:
            if st.button("Next ➡️", type="primary", use_container_width=True, key="wiz_next_2"):
                st.session_state.create_wizard_step = 3
                st.rerun()

    elif step == 3:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        # Two column layout: inputs on left, preview on right
        col_left, col_right = st.columns([1.1, 0.9])
        
        with col_left:
            st.markdown("<div style='font-size: 1.1rem; font-weight: 700; color: #1E2A44; margin-bottom: 12px;'>Choose template and title</div>", unsafe_allow_html=True)
            res_title = st.text_input("Resume Title", value=st.session_state.get("wizard_resume_title", ""), placeholder="e.g. Frontend Developer Resume")
            st.session_state.wizard_resume_title = res_title
            
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            st.markdown("**Select Template Theme**")
            tpl_options = list(TEMPLATES.keys())
            tpl_names = {k: v["name"] for k, v in TEMPLATES.items()}
            
            sel_tpl = st.selectbox("Template Theme", options=tpl_options, format_func=lambda k: tpl_names[k])
            st.session_state.wizard_template = sel_tpl
            
        with col_right:
            st.markdown("<div style='font-size: 0.9rem; font-weight: 700; color: #1E2A44; margin-bottom: 8px;'>Template Preview</div>", unsafe_allow_html=True)
            st.info("Preview not available.")
                
        st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
        w3_col1, w3_col2 = st.columns(2)
        with w3_col1:
            if st.button("⬅️ Back", use_container_width=True, key="wiz_back_3"):
                st.session_state.create_wizard_step = 2
                st.rerun()
        with w3_col2:
            if st.button("🚀 Create Resume", type="primary", use_container_width=True):
                title = res_title.strip() or f"{st.session_state.wizard_resume_type} Resume"
                clean_title = re.sub(r"[^a-zA-Z0-9\s_-]", "", title).strip()
                file_base = clean_title.lower().replace(" ", "_")
                PROJECT_ROOT = st.session_state.get("PROJECT_ROOT", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                new_path = os.path.join(PROJECT_ROOT, "exports", "json", f"{file_base}.json")
                counter = 1
                while os.path.exists(new_path):
                    new_path = os.path.join(PROJECT_ROOT, "exports", "json", f"{file_base}_{counter}.json")
                    counter += 1
                    
                content = copy.deepcopy(st.session_state.DEFAULT_RESUME)
                
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
                    from resume_builder.services.github import GitHubIntegration
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
                    "color": "#6366F1",
                    "margins": 20,
                    "fscale": 1.0,
                    "fitting": "Auto Compress",
                    "last_edited": time.time()
                }
                
                with open(new_path, "w", encoding="utf-8") as f:
                    json.dump(content, f, indent=2)
                    
                st.session_state.create_wizard_step = 1
                st.session_state.wizard_just_opened = True  # Reset for next open
                st.session_state.show_create_dialog = False
                if "wizard_uploaded_file" in st.session_state:
                    del st.session_state.wizard_uploaded_file
                if "wizard_github_repos" in st.session_state:
                    del st.session_state.wizard_github_repos
                    
                st.session_state.load_active_resume_fn(new_path)
                st.session_state.navigation_page = "workspace"
                st.session_state.editor_step = 0
                st.rerun()
