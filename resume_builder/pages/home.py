import streamlit as st
import os
import re
import json
import time
import html

from resume_builder.services.storage import list_resumes, load_active_resume
from resume_builder.utils.helpers import format_relative_time

# Import components
from resume_builder.components.navbar import render_navbar
from resume_builder.components.sidebar import render_sidebar
from resume_builder.components.hero import render_hero
from resume_builder.components.search_bar import render_search_bar_desktop, render_search_bar_mobile
from resume_builder.components.resume_card import (
    render_resume_grid_card,
    render_continue_card_desktop,
    render_continue_card_mobile,
)
from resume_builder.components.bottom_nav import render_bottom_nav
from resume_builder.components.wizard import show_create_resume_dialog

# Import template registry
from resume_builder.templates import TEMPLATES as ALL_TEMPLATES

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def show_home():
    """Phase 1: My Resumes Dashboard containing Recent Resumes card grid."""
    
    # 1. Hidden marker for CSS targeting
    st.markdown('<div id="dashboard-marker"></div>', unsafe_allow_html=True)
    
    # 2. Top Navigation Bar & Left Sidebar
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
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 24px 0;
          gap: 20px;
          z-index: 999;
          transition: width 0.2s ease, padding 0.2s ease;
          box-shadow: 2px 0 10px rgba(0,0,0,0.01);
          font-family: 'Inter', sans-serif;
          box-sizing: border-box;
        }
        .rb-sidebar-item {
          width: 44px; height: 44px; display: flex; align-items: center;
          justify-content: center; border-radius: 8px; color: #64748B;
          cursor: pointer; transition: all 0.2s; position: relative;
          text-decoration: none;
        }
        .rb-sidebar-item:hover, .rb-sidebar-item.active {
          background: #F8F5EF; color: #A47148;
        }
        .rb-sidebar-icon { font-size: 1.25rem; line-height: 1; }
        .rb-sidebar-label {
          position: absolute; left: 56px; background: #1E293B;
          color: #fff; padding: 6px 10px; border-radius: 4px;
          font-size: 0.75rem; font-weight: 500; opacity: 0;
          pointer-events: none; transition: opacity 0.15s;
          white-space: nowrap; box-shadow: 0 4px 12px rgba(0,0,0,0.1);
          z-index: 1001;
        }
        .rb-sidebar-item:hover .rb-sidebar-label { opacity: 1; }

        /* Sidebar Expansion State */
        .rb-sidebar.expanded {
          width: 240px;
          align-items: stretch;
          padding: 24px 16px;
        }
        .rb-sidebar.expanded .rb-sidebar-item {
          width: 100%;
          justify-content: flex-start;
          padding: 0 16px;
          gap: 12px;
          box-sizing: border-box;
        }
        .rb-sidebar.expanded .rb-sidebar-label {
          position: static;
          background: transparent;
          color: inherit;
          padding: 0;
          box-shadow: none;
          opacity: 1;
          pointer-events: auto;
          font-size: 0.875rem;
          font-weight: 500;
        }

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
        }
        </style>
        """,
        unsafe_allow_html=True
    )
        
    try:
        render_navbar()
    except Exception as e:
        st.error(f"Component failed (navbar): {e}")
    try:
        render_sidebar()
    except Exception as e:
        st.error(f"Component failed (sidebar): {e}")
        
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
    
    try:
        render_hero()
    except Exception as e:
        st.error(f"Component failed: {e}")

    # 4. Search & Filter Section (Desktop)
    try:
        render_search_bar_desktop(search_query)
    except Exception as e:
        st.error(f"Component failed: {e}")

    # 4. Search & Filter Section (Mobile)
    try:
        render_search_bar_mobile(search_query)
    except Exception as e:
        st.error(f"Component failed: {e}")
    
    # Filter matching resumes (shared logic)
    if search_query:
        search_query_clean = search_query.strip().lower()
        resumes = [r for r in resumes if search_query_clean in r["title"].lower() or search_query_clean in r["template"].lower()]

    # 5. Continue Editing (Desktop)
    if resumes:
        latest = resumes[0]
        rel_time = format_relative_time(latest["last_edited"])
        tpl_disp = ALL_TEMPLATES.get(latest["template"], {}).get("name", latest["template"])
        
        st.markdown('<div class="section-header-row"><span class="section-title">Continue Editing</span></div>', unsafe_allow_html=True)
        st.markdown('<div id="continue-card-marker"></div>', unsafe_allow_html=True)
        
        c_col1, c_col2 = st.columns([4.2, 0.8])
        with c_col1:
            try:
                render_continue_card_desktop(latest, tpl_disp, rel_time)
            except Exception as e:
                st.error(f"Component failed (continue card desktop): {e}")
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
        try:
            render_continue_card_mobile(latest, tpl_disp, rel_time)
        except Exception as e:
            st.error(f"Component failed (continue card mobile): {e}")
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
                    try:
                        render_resume_grid_card(r, tpl_disp, rel_time)
                    except Exception as e:
                        st.error(f"Component failed (resume grid card): {e}")
                    
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
    st.markdown('<div id="btn-dashed-create-arrow-wrapper" style="display:none;">', unsafe_allow_html=True)
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
              const createBtn = parentDoc.querySelector('#btn-dashed-create-arrow-wrapper button');
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
                const createBtn = parentDoc.querySelector('#btn-dashed-create-arrow-wrapper button');
                if (createBtn) createBtn.click();
              });
            }
          }
        
          ['tpl-ats', 'tpl-modern', 'tpl-minimal', 'tpl-creative'].forEach(id => {
            const card = parentDoc.getElementById(id);
            if (card && !card.dataset.navSetup) {
              card.dataset.navSetup = "true";
              card.addEventListener('click', () => {
                const btn = parentDoc.querySelector('#btn-dashed-create-arrow-wrapper button');
                if (btn) btn.click();
              });
            }
          });
          
          const dashedCreate = parentDoc.getElementById('btn-dashed-create-card-trigger');
          if (dashedCreate && !dashedCreate.dataset.clickSetup) {
            dashedCreate.dataset.clickSetup = "true";
            dashedCreate.addEventListener('click', () => {
              const createBtn = parentDoc.querySelector('#btn-dashed-create-arrow-wrapper button');
              if (createBtn) createBtn.click();
            });
          }

          // Mobile FAB setup
          const mobFab = parentDoc.getElementById('mob-fab-trigger');
          if (mobFab && !mobFab.dataset.clickSetup) {
            mobFab.dataset.clickSetup = "true";
            mobFab.addEventListener('click', () => {
              const createBtn = parentDoc.querySelector('#btn-dashed-create-arrow-wrapper button');
              if (createBtn) createBtn.click();
            });
          }

          // Mobile Dashed Create Card triggers
          const mobDashedCreates = parentDoc.querySelectorAll('.mob-dashed-create-card');
          mobDashedCreates.forEach(el => {
            if (el && !el.dataset.clickSetup) {
              el.dataset.clickSetup = "true";
              el.addEventListener('click', () => {
                const createBtn = parentDoc.querySelector('#btn-dashed-create-arrow-wrapper button');
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
              const createBtn = parentDoc.querySelector('#btn-dashed-create-arrow-wrapper button');
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
              const createBtn = parentDoc.querySelector('#btn-dashed-create-arrow-wrapper button');
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
