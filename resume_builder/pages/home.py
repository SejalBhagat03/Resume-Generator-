import streamlit as st
from resume_builder.utils.helpers import clean_html, format_relative_time
import os
import re
import json
import time
import html
import textwrap

from resume_builder.services.storage import list_resumes, load_active_resume
# Import components
from resume_builder.components.navbar import render_navbar
from resume_builder.components.sidebar import render_sidebar
from resume_builder.components.hero import render_hero_desktop, render_hero_mobile
from resume_builder.components.search_bar import render_search_bar_desktop, render_search_bar_mobile
from resume_builder.components.resume_card import (
    render_resume_grid_card,
    render_continue_card_desktop,
    render_continue_card_mobile,
)
from resume_builder.components.bottom_nav import render_bottom_nav
from resume_builder.components.wizard import show_create_resume_dialog
from resume_builder.components.stats_card import render_desktop_stats, render_mobile_stats
from resume_builder.components.copilot_card import render_copilot_card

# Import template registry
from resume_builder.templates import TEMPLATES as ALL_TEMPLATES

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def show_home():
    """Main homepage router that handles device-specific rendering and shared state."""
    
    # Render viewport detection script to dynamically sync mobile view based on window size
    st.markdown(
        clean_html(
            """
            <script>
            (function() {
              function checkViewport() {
                try {
                  const parentWin = window.parent || window;
                  const isMobileViewport = parentWin.innerWidth < 768;
                  const currentUrl = new URL(parentWin.location.href);
                  const hasMobileParam = currentUrl.searchParams.has("mobile");
                  const isMobileParam = currentUrl.searchParams.get("mobile") === "true";
                  
                  if (!hasMobileParam || isMobileViewport !== isMobileParam) {
                    currentUrl.searchParams.set("mobile", isMobileViewport ? "true" : "false");
                    parentWin.location.replace(currentUrl.href);
                  }
                } catch (e) {
                  // Fallback for sandboxed or cross-origin environments
                  const isMobileViewport = window.innerWidth < 768;
                  const currentUrl = new URL(window.location.href);
                  const hasMobileParam = currentUrl.searchParams.has("mobile");
                  const isMobileParam = currentUrl.searchParams.get("mobile") === "true";
                  
                  if (!hasMobileParam || isMobileViewport !== isMobileParam) {
                    currentUrl.searchParams.set("mobile", isMobileViewport ? "true" : "false");
                    window.location.replace(currentUrl.href);
                  }
                }
              }
              checkViewport();
              try {
                const parentWin = window.parent || window;
                let resizeTimeout;
                parentWin.addEventListener('resize', () => {
                  clearTimeout(resizeTimeout);
                  resizeTimeout = setTimeout(checkViewport, 200);
                });
              } catch (e) {
                let resizeTimeout;
                window.addEventListener('resize', () => {
                  clearTimeout(resizeTimeout);
                  resizeTimeout = setTimeout(checkViewport, 200);
                });
              }
            })();
            </script>
            """
        ),
        unsafe_allow_html=True
    )
    
    # 1. Viewport-based layout detection via query parameters & User-Agent fallback
    is_mobile = False
    query_mobile = st.query_params.get("mobile")
    if query_mobile is not None:
        is_mobile = (query_mobile == "true")
    else:
        if hasattr(st, "context") and st.context.headers:
            ua = st.context.headers.get("User-Agent", "").lower()
            is_mobile = any(kw in ua for kw in ["mobile", "android", "iphone", "ipad", "phone"])
            
    st.session_state.is_mobile = is_mobile

    resumes = list_resumes()
    
    # Sync search query states
    search_query = st.session_state.get("search_query_state", "")
    if "search_resumes_val" in st.session_state and st.session_state.search_resumes_val != search_query:
        st.session_state.search_query_state = st.session_state.search_resumes_val
        search_query = st.session_state.search_resumes_val
    elif "mob_search_resumes_val" in st.session_state and st.session_state.mob_search_resumes_val != search_query:
        st.session_state.search_query_state = st.session_state.mob_search_resumes_val
        search_query = st.session_state.mob_search_resumes_val

    # Filter matching resumes
    filtered_resumes = resumes
    if search_query:
        search_query_clean = search_query.strip().lower()
        filtered_resumes = [
            r for r in resumes 
            if search_query_clean in r["title"].lower() or search_query_clean in r["template"].lower()
        ]

    # Save resumes_list in session state for copilot triggers
    st.session_state.resumes_list = resumes

    # Render appropriate home layout
    if st.session_state.is_mobile:
        render_mobile_home(resumes, filtered_resumes, search_query)
    else:
        render_desktop_home(resumes, filtered_resumes, search_query)

    # Render wizard dialog if active (shared across layouts)
    if st.session_state.get("show_create_dialog", False):
        show_create_resume_dialog()


def render_desktop_home(resumes, filtered_resumes, search_query):
    """Renders the desktop dashboard view."""
    st.markdown('<div id="dashboard-marker"></div>', unsafe_allow_html=True)
    
    # Render layout wrappers
    try:
        render_navbar()
    except Exception as e:
        st.error(f"Navbar failed to render: {e}")
        
    try:
        render_sidebar()
    except Exception as e:
        st.error(f"Sidebar failed to render: {e}")
        
    st.markdown(
        clean_html(
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
    
              function syncParentPadding(w) {
                try {
                  window.parent.document.documentElement.style.setProperty('--sidebar-w', w);
                } catch(e) {}
              }
    
          var sidebar = window.parent.document.getElementById('rb-sidebar');
          var overlay = window.parent.document.getElementById('rb-overlay');
          var hamburger = window.parent.document.getElementById('rb-hamburger');

          if (sidebar) {
            // Force Canva-style mini rail
            sidebar.classList.remove('expanded');
            syncParentPadding(COLLAPSED);
          }

          if (hamburger) {
            hamburger.addEventListener('click', function() {
              if (!isDesktop()) {
                sidebar.classList.toggle('expanded');
                if (overlay) {
                  overlay.classList.toggle('active', sidebar.classList.contains('expanded'));
                }
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
            """
        ),
        unsafe_allow_html=True
    )

    # Hero
    render_hero_desktop()

    # Stats cards
    render_desktop_stats()

    # Search section
    render_search_bar_desktop(search_query)

    # Continue Editing
    if filtered_resumes:
        latest = filtered_resumes[0]
        rel_time = format_relative_time(latest["last_edited"])
        tpl_disp = ALL_TEMPLATES.get(latest["template"], {}).get("name", latest["template"])
        
        import datetime
        mod_date = datetime.datetime.fromtimestamp(latest["last_edited"]).strftime("%d %b %Y")
        
        st.markdown('<div class="section-header-row continue-section-desktop-title"><span class="section-title">Continue Editing</span><span class="view-all-link">View All</span></div>', unsafe_allow_html=True)
        st.markdown('<div id="continue-card-marker"></div>', unsafe_allow_html=True)
        
        c_col1, c_col2 = st.columns([3.2, 1.8])
        with c_col1:
            try:
                render_continue_card_desktop(latest, tpl_disp, rel_time, mod_date)
            except Exception as e:
                st.error(f"Component failed (continue card desktop): {e}")
        with c_col2:
            st.markdown('<div class="continue-actions-desktop-row">', unsafe_allow_html=True)
            act_col1, act_col2 = st.columns([3.5, 1])
            with act_col1:
                if st.button("⚡ Continue Editing", key="btn_continue_text", use_container_width=True):
                    load_active_resume(latest["path"])
                    st.session_state.navigation_page = "workspace"
                    st.session_state.editor_step = 0
                    st.rerun()
            with act_col2:
                with st.popover("⋮", key="continue_options_popover", use_container_width=True):
                    new_title = st.text_input("Rename:", value=latest["title"], key="rename_continue_desktop")
                    if new_title.strip() != latest["title"]:
                        with open(latest["path"], "r", encoding="utf-8") as f:
                            content = json.load(f)
                        content.setdefault("metadata", {})["title"] = new_title.strip()
                        content["metadata"]["last_edited"] = time.time()
                        with open(latest["path"], "w", encoding="utf-8") as f:
                            json.dump(content, f, indent=2)
                        st.rerun()
                    if st.button("👥 Duplicate", key="dup_continue_desktop", use_container_width=True):
                        base_name = os.path.splitext(os.path.basename(latest["path"]))[0]
                        new_path = os.path.join(PROJECT_ROOT, "exports", "json", f"{base_name}_copy.json")
                        counter = 1
                        while os.path.exists(new_path):
                            new_path = os.path.join(PROJECT_ROOT, "exports", "json", f"{base_name}_copy_{counter}.json")
                            counter += 1
                        with open(latest["path"], "r", encoding="utf-8") as f:
                            content = json.load(f)
                        content.setdefault("metadata", {})["title"] = f"{latest['title']} Copy"
                        content["metadata"]["last_edited"] = time.time()
                        with open(new_path, "w", encoding="utf-8") as f:
                            json.dump(content, f, indent=2)
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # Popular Templates Section
    st.markdown('<div class="section-header-row template-section-marker"><span class="section-title">Popular Templates</span><span class="view-all-link">View All &rsaquo;</span></div>', unsafe_allow_html=True)
    st.markdown(
        clean_html(
            """
            <div class="template-scroll-container">
              <!-- Template Card 1 -->
              <div class="template-scroll-card" id="tpl-ats">
                <div class="template-scroll-thumb">
                  <svg width="60" height="80" viewBox="0 0 24 30" fill="none" xmlns="http://www.w3.org/2000/svg" style="border: 1px solid #E2E8F0; border-radius: 4px; background: #fff;"><rect x="2" y="2" width="20" height="26" rx="1" fill="#FFFFFF"/><line x1="4" y1="6" x2="20" y2="6" stroke="#E2E8F0" stroke-width="1.5"/><line x1="4" y1="10" x2="14" y2="10" stroke="#E2E8F0" stroke-width="1.5"/><line x1="4" y1="14" x2="18" y2="14" stroke="#E2E8F0" stroke-width="1.5"/></svg>
                  <div class="template-select-indicator" id="ind-ats">✓</div>
                </div>
                <div class="template-scroll-name">ATS Professional</div>
              </div>
              
              <!-- Template Card 2 -->
              <div class="template-scroll-card" id="tpl-modern">
                <div class="template-scroll-thumb">
                  <svg width="60" height="80" viewBox="0 0 24 30" fill="none" xmlns="http://www.w3.org/2000/svg" style="border: 1px solid #E2E8F0; border-radius: 4px; background: #fff;"><rect x="2" y="2" width="20" height="26" rx="1" fill="#FFFFFF"/><rect x="4" y="4" width="16" height="5" rx="0.5" fill="#A47148" opacity="0.1"/><line x1="4" y1="13" x2="20" y2="13" stroke="#E2E8F0" stroke-width="1.5"/><line x1="4" y1="17" x2="16" y2="17" stroke="#E2E8F0" stroke-width="1.5"/></svg>
                  <div class="template-select-indicator" id="ind-modern">✓</div>
                </div>
                <div class="template-scroll-name">Modern</div>
              </div>
              
              <!-- Template Card 3 -->
              <div class="template-scroll-card" id="tpl-minimal">
                <div class="template-scroll-thumb">
                  <svg width="60" height="80" viewBox="0 0 24 30" fill="none" xmlns="http://www.w3.org/2000/svg" style="border: 1px solid #E2E8F0; border-radius: 4px; background: #fff;"><rect x="2" y="2" width="20" height="26" rx="1" fill="#FFFFFF"/><line x1="4" y1="8" x2="12" y2="8" stroke="#1E293B" stroke-width="2"/><line x1="4" y1="14" x2="20" y2="14" stroke="#E2E8F0" stroke-width="1.5"/><line x1="4" y1="18" x2="18" y2="18" stroke="#E2E8F0" stroke-width="1.5"/></svg>
                  <div class="template-select-indicator" id="ind-minimal">✓</div>
                </div>
                <div class="template-scroll-name">Minimal</div>
              </div>
              
              <!-- Template Card 4 -->
              <div class="template-scroll-card" id="tpl-creative">
                <div class="template-scroll-thumb">
                  <svg width="60" height="80" viewBox="0 0 24 30" fill="none" xmlns="http://www.w3.org/2000/svg" style="border: 1px solid #E2E8F0; border-radius: 4px; background: #fff;"><rect x="2" y="2" width="20" height="26" rx="1" fill="#FFFFFF"/><rect x="4" y="4" width="6" height="22" fill="#E8F5E9"/><line x1="12" y1="6" x2="20" y2="6" stroke="#E2E8F0" stroke-width="1.5"/><line x1="12" y1="10" x2="18" y2="10" stroke="#E2E8F0" stroke-width="1.5"/></svg>
                  <div class="template-select-indicator" id="ind-creative">✓</div>
                </div>
                <div class="template-scroll-name">Creative</div>
              </div>
            </div>
            """
        ),
        unsafe_allow_html=True
    )

    # My Resumes Grid
    st.markdown('<div class="section-header-row resumes-section-marker"><span class="section-title">My Resumes</span><div class="resumes-controls-desktop"><span class="sort-label">Sort by: <b>Recent</b> &nbsp;&nbsp;&nbsp;</span><div class="layout-toggle-btn active">&#x25A6;</div><div class="layout-toggle-btn">&#x2261;</div></div></div>', unsafe_allow_html=True)
    
    if not filtered_resumes:
        st.info("No resumes found.")
        st.markdown(
            clean_html(
                """
                <div class="dashed-create-card">
                  <div class="dashed-create-circle">＋</div>
                  <div class="dashed-create-title">Create New Resume</div>
                  <div class="dashed-create-desc">Start from scratch or choose a template</div>
                </div>
                """
            ),
            unsafe_allow_html=True
        )
        if st.button("Create New", key="btn_create_new_grid_empty", use_container_width=True):
            st.session_state.wizard_just_opened = True
            st.session_state.show_create_dialog = True
            st.rerun()
    else:
        st.markdown('<div id="my-resumes-grid-marker"></div>', unsafe_allow_html=True)
        for idx, r in enumerate(filtered_resumes):
            tpl_disp = ALL_TEMPLATES.get(r["template"], {}).get("name", r["template"])
            rel_time = format_relative_time(r["last_edited"])
            
            with st.container():
                try:
                    render_resume_grid_card(r, tpl_disp, rel_time)
                except Exception as e:
                    st.error(f"Component failed (resume grid card): {e}")
                
                act_col1, act_col2, act_col3 = st.columns([1.2, 1.2, 0.8])
                with act_col1:
                    if st.button("✏️ Edit", key=f"grid_edit_{idx}", use_container_width=True):
                        load_active_resume(r["path"])
                        st.session_state.navigation_page = "workspace"
                        st.session_state.editor_step = 0
                        st.rerun()
                with act_col2:
                    pdf_file_path = os.path.join(PROJECT_ROOT, "exports", "pdf", os.path.splitext(os.path.basename(r["path"]))[0] + ".pdf")
                    if os.path.exists(pdf_file_path):
                        with open(pdf_file_path, "rb") as pf:
                            pdf_data = pf.read()
                        safe_title = re.sub(r"[^a-zA-Z0-9]", "_", r["title"])
                        st.download_button(
                            "📥 PDF",
                            data=pdf_data,
                            file_name=f"{safe_title}_Resume.pdf",
                            mime="application/pdf",
                            key=f"grid_dl_pdf_{idx}",
                            use_container_width=True
                        )
                    else:
                        st.button("📥 PDF", key=f"grid_dl_pdf_disabled_{idx}", disabled=True, use_container_width=True)
                with act_col3:
                    with st.popover("⋮", key=f"grid_options_{idx}", use_container_width=True):
                        new_title = st.text_input("Rename:", value=r["title"], key=f"rename_input_{idx}")
                        if new_title.strip() != r["title"]:
                            with open(r["path"], "r", encoding="utf-8") as f:
                                content = json.load(f)
                            content.setdefault("metadata", {})["title"] = new_title.strip()
                            content["metadata"]["last_edited"] = time.time()
                            with open(r["path"], "w", encoding="utf-8") as f:
                                json.dump(content, f, indent=2)
                            st.rerun()
                            
                        if st.button("👥 Duplicate", key=f"btn_dup_pop_{idx}", use_container_width=True):
                            base_name = os.path.splitext(os.path.basename(r["path"]))[0]
                            new_path = os.path.join(PROJECT_ROOT, "exports", "json", f"{base_name}_copy.json")
                            counter = 1
                            while os.path.exists(new_path):
                                new_path = os.path.join(PROJECT_ROOT, "exports", "json", f"{base_name}_copy_{counter}.json")
                                counter += 1
                            with open(r["path"], "r", encoding="utf-8") as f:
                                content = json.load(f)
                            content.setdefault("metadata", {})["title"] = f"{r['title']} Copy"
                            content["metadata"]["last_edited"] = time.time()
                            with open(new_path, "w", encoding="utf-8") as f:
                                json.dump(content, f, indent=2)
                            st.rerun()
                            
                        is_root = (os.path.abspath(r["path"]) == os.path.abspath(os.path.join(PROJECT_ROOT, "exports", "json", "resume.json")))
                        if st.button("🗑️ Delete", key=f"btn_del_pop_{idx}", use_container_width=True, disabled=is_root):
                            if os.path.exists(r["path"]):
                                os.remove(r["path"])
                            if os.path.exists(pdf_file_path):
                                os.remove(pdf_file_path)
                            st.rerun()
        
        # Append Dashed Card at the end
        st.markdown(
            clean_html(
                """
                <div class="dashed-create-card">
                  <div class="dashed-create-circle">＋</div>
                  <div class="dashed-create-title">Create New Resume</div>
                  <div class="dashed-create-desc">Start from scratch or choose a template</div>
                </div>
                """
            ),
            unsafe_allow_html=True
        )
        if st.button("Create New", key="btn_create_new_grid", use_container_width=True):
            st.session_state.wizard_just_opened = True
            st.session_state.show_create_dialog = True
            st.rerun()

    # Hidden elements trigger setup
    st.markdown('<div id="btn-dashed-create-arrow-wrapper" style="display:none;">', unsafe_allow_html=True)
    if st.button("", key="btn_dashed_create_arrow"):
        st.session_state.wizard_just_opened = True
        st.session_state.show_create_dialog = True
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Load popular template interactions JS helper
    render_js_actions()


def render_mobile_home(resumes, filtered_resumes, search_query):
    """Renders the mobile layout view."""
    st.markdown('<div id="mob-dashboard-marker"></div>', unsafe_allow_html=True)
    
    # Top navigation
    try:
        render_navbar()
    except Exception as e:
        st.error(f"Navbar failed to render: {e}")

    # Hero
    render_hero_mobile()

    # Stats card
    render_mobile_stats()

    # Copilot section
    render_copilot_card()

    # Search section
    render_search_bar_mobile(search_query)

    # Continue Editing (Mobile)
    if filtered_resumes:
        latest = filtered_resumes[0]
        rel_time = format_relative_time(latest["last_edited"])
        tpl_disp = ALL_TEMPLATES.get(latest["template"], {}).get("name", latest["template"])
        
        st.markdown('<div class="mob-section-header-row mob-continue-section-marker"><span class="mob-section-title">Continue Editing</span><span class="mob-view-all-link">View All &rsaquo;</span></div>', unsafe_allow_html=True)
        try:
            render_continue_card_mobile(latest, tpl_disp, rel_time)
        except Exception as e:
            st.error(f"Component failed (continue card mobile): {e}")
            
        st.markdown('<div class="mob-continue-actions-overlay">', unsafe_allow_html=True)
        mob_c_col1, mob_c_col2 = st.columns([3.2, 1.8])
        with mob_c_col1:
            if st.button("⚡ Continue", key="mob_btn_continue_text", use_container_width=True):
                load_active_resume(latest["path"])
                st.session_state.navigation_page = "workspace"
                st.session_state.editor_step = 0
                st.rerun()
        with mob_c_col2:
            with st.popover("⋮", key="mob_continue_options_popover", use_container_width=True):
                new_title = st.text_input("Rename:", value=latest["title"], key="rename_continue_mobile")
                if new_title.strip() != latest["title"]:
                    with open(latest["path"], "r", encoding="utf-8") as f:
                        content = json.load(f)
                    content.setdefault("metadata", {})["title"] = new_title.strip()
                    content["metadata"]["last_edited"] = time.time()
                    with open(latest["path"], "w", encoding="utf-8") as f:
                        json.dump(content, f, indent=2)
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Popular Templates Section
    st.markdown('<div class="mob-section-header-row"><span class="mob-section-title">Popular Templates</span><span class="mob-view-all-link">View All &rsaquo;</span></div>', unsafe_allow_html=True)
    st.markdown(
        textwrap.dedent(
            """
            <div class="template-scroll-container">
              <!-- Template Card 1 -->
              <div class="template-scroll-card" id="tpl-ats">
                <div class="template-scroll-thumb">
                  <svg width="60" height="80" viewBox="0 0 24 30" fill="none" xmlns="http://www.w3.org/2000/svg" style="border: 1px solid #E2E8F0; border-radius: 4px; background: #fff;"><rect x="2" y="2" width="20" height="26" rx="1" fill="#FFFFFF"/><line x1="4" y1="6" x2="20" y2="6" stroke="#E2E8F0" stroke-width="1.5"/><line x1="4" y1="10" x2="14" y2="10" stroke="#E2E8F0" stroke-width="1.5"/><line x1="4" y1="14" x2="18" y2="14" stroke="#E2E8F0" stroke-width="1.5"/></svg>
                  <div class="template-select-indicator" id="ind-ats">✓</div>
                </div>
                <div class="template-scroll-name">ATS Professional</div>
              </div>
              
              <!-- Template Card 2 -->
              <div class="template-scroll-card" id="tpl-modern">
                <div class="template-scroll-thumb">
                  <svg width="60" height="80" viewBox="0 0 24 30" fill="none" xmlns="http://www.w3.org/2000/svg" style="border: 1px solid #E2E8F0; border-radius: 4px; background: #fff;"><rect x="2" y="2" width="20" height="26" rx="1" fill="#FFFFFF"/><rect x="4" y="4" width="16" height="5" rx="0.5" fill="#A47148" opacity="0.1"/><line x1="4" y1="13" x2="20" y2="13" stroke="#E2E8F0" stroke-width="1.5"/><line x1="4" y1="17" x2="16" y2="17" stroke="#E2E8F0" stroke-width="1.5"/></svg>
                  <div class="template-select-indicator" id="ind-modern">✓</div>
                </div>
                <div class="template-scroll-name">Modern</div>
              </div>
              
              <!-- Template Card 3 -->
              <div class="template-scroll-card" id="tpl-minimal">
                <div class="template-scroll-thumb">
                  <svg width="60" height="80" viewBox="0 0 24 30" fill="none" xmlns="http://www.w3.org/2000/svg" style="border: 1px solid #E2E8F0; border-radius: 4px; background: #fff;"><rect x="2" y="2" width="20" height="26" rx="1" fill="#FFFFFF"/><line x1="4" y1="8" x2="12" y2="8" stroke="#1E293B" stroke-width="2"/><line x1="4" y1="14" x2="20" y2="14" stroke="#E2E8F0" stroke-width="1.5"/><line x1="4" y1="18" x2="18" y2="18" stroke="#E2E8F0" stroke-width="1.5"/></svg>
                  <div class="template-select-indicator" id="ind-minimal">✓</div>
                </div>
                <div class="template-scroll-name">Minimal</div>
              </div>
              
              <!-- Template Card 4 -->
              <div class="template-scroll-card" id="tpl-creative">
                <div class="template-scroll-thumb">
                  <svg width="60" height="80" viewBox="0 0 24 30" fill="none" xmlns="http://www.w3.org/2000/svg" style="border: 1px solid #E2E8F0; border-radius: 4px; background: #fff;"><rect x="2" y="2" width="20" height="26" rx="1" fill="#FFFFFF"/><rect x="4" y="4" width="6" height="22" fill="#E8F5E9"/><line x1="12" y1="6" x2="20" y2="6" stroke="#E2E8F0" stroke-width="1.5"/><line x1="12" y1="10" x2="18" y2="10" stroke="#E2E8F0" stroke-width="1.5"/></svg>
                  <div class="template-select-indicator" id="ind-creative">✓</div>
                </div>
                <div class="template-scroll-name">Creative</div>
              </div>
            </div>
            """
        ),
        unsafe_allow_html=True
    )

    # My Resumes (Mobile Stacked List)
    st.markdown('<div class="mob-section-header-row mob-resumes-section-marker"><span class="mob-section-title">My Resumes</span><div class="mob-resumes-controls"><span class="mob-sort-label">Sort: Recent &nbsp;&nbsp;</span><div class="mob-grid-icon active">&#x25A6;</div></div></div>', unsafe_allow_html=True)
    
    if not filtered_resumes:
        st.markdown(
            textwrap.dedent(
                """
                <div class="mob-dashed-create-card">
                    <div class="mob-dashed-create-icon">&#x2795;</div>
                    <div class="mob-dashed-create-text">Create New Resume</div>
                </div>
                """
            ),
            unsafe_allow_html=True
        )
        if st.button("Create New", key="btn_mob_create_empty", use_container_width=True):
            st.session_state.wizard_just_opened = True
            st.session_state.show_create_dialog = True
            st.rerun()
    else:
        for idx, r in enumerate(filtered_resumes):
            tpl_disp = ALL_TEMPLATES.get(r["template"], {}).get("name", r["template"])
            rel_time = format_relative_time(r["last_edited"])
            color = r.get("color", "#A86A3D")
            
            st.markdown(
                textwrap.dedent(
                    f"""
                    <div class="mob-resume-card-container">
                        <div class="mob-resume-card-left">
                            <div class="mob-resume-card-thumb">
                                <div class="mini-resume-page-flat-mob-list">
                                    <div class="mini-flat-header-mob-list" style="background: {color};"></div>
                                    <div class="mini-flat-body-mob-list">
                                        <div class="mini-flat-line-mob-list"></div>
                                    </div>
                                </div>
                            </div>
                            <div class="mob-resume-card-info">
                                <div class="mob-resume-card-title">{html.escape(r["title"])}</div>
                                <div class="mob-resume-card-meta">
                                    <span class="mob-resume-card-badge">{tpl_disp}</span>
                                    <span class="mob-resume-card-time">Updated {rel_time}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    """
                ),
                unsafe_allow_html=True
            )
            
            mob_act_col1, mob_act_col2 = st.columns([3, 1])
            with mob_act_col1:
                if st.button("✏️ Edit", key=f"mob_grid_edit_{idx}", use_container_width=True):
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
                    is_root = (os.path.abspath(r["path"]) == os.path.abspath(os.path.join(PROJECT_ROOT, "exports", "json", "resume.json")))
                    if st.button("🗑️ Delete", key=f"mob_btn_del_pop_{idx}", use_container_width=True, disabled=is_root):
                        if os.path.exists(r["path"]):
                            os.remove(r["path"])
                        st.rerun()
                        
        # Mobile creation card at end
        st.markdown(
            clean_html(
                """
                <div class="mob-dashed-create-card">
                    <div class="mob-dashed-create-icon">&#x2795;</div>
                    <div class="mob-dashed-create-text">Create New Resume</div>
                </div>
                """
            ),
            unsafe_allow_html=True
        )
        if st.button("Create New", key="btn_mob_create_end", use_container_width=True):
            st.session_state.wizard_just_opened = True
            st.session_state.show_create_dialog = True
            st.rerun()

    # Hidden trigger
    st.markdown('<div id="btn-dashed-create-arrow-wrapper" style="display:none;">', unsafe_allow_html=True)
    if st.button("", key="btn_dashed_create_arrow"):
        st.session_state.wizard_just_opened = True
        st.session_state.show_create_dialog = True
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # FAB (Mobile Only)
    st.markdown('<div class="mob-fab" id="mob-fab-trigger">＋</div>', unsafe_allow_html=True)

    # Sticky bottom navigation
    render_bottom_nav()

    # Mobile Actions JS
    render_js_actions()


def render_js_actions():
    """Renders basic event listeners and popular template highlighting."""
    active_tpl = st.session_state.get("template", "sejal_original")
    st.markdown(
        clean_html(
            f"""
            <script>
            (function() {{
              const parentDoc = window.parent.document;
              
              const templates = ['ats', 'modern', 'minimal', 'creative'];
              templates.forEach(t => {{
                const indicator = parentDoc.getElementById('ind-' + t);
                if (indicator) {{
                  const isSelected = ('{active_tpl}' === t || ('{active_tpl}' === 'sejal_original' && t === 'ats'));
                  indicator.style.display = isSelected ? 'flex' : 'none';
                  
                  const card = parentDoc.getElementById('tpl-' + t);
                  if (card) {{
                    card.classList.toggle('selected', isSelected);
                  }}
                }}
              }});
              
              function setupNavigation() {{
                const sbHome = parentDoc.getElementById('sb-home');
                if (sbHome && !sbHome.dataset.navSetup) {{
                  sbHome.dataset.navSetup = "true";
                  sbHome.addEventListener('click', () => {{
                    parentDoc.querySelector('.main .block-container')?.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                  }});
                }}
                
                const sbResumes = parentDoc.getElementById('sb-resumes');
                if (sbResumes && !sbResumes.dataset.navSetup) {{
                  sbResumes.dataset.navSetup = "true";
                  sbResumes.addEventListener('click', () => {{
                    parentDoc.querySelector('.resumes-section-marker')?.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                  }});
                }}
                
                const sbTemplates = parentDoc.getElementById('sb-templates');
                if (sbTemplates && !sbTemplates.dataset.navSetup) {{
                  sbTemplates.dataset.navSetup = "true";
                  sbTemplates.addEventListener('click', () => {{
                    parentDoc.querySelector('.template-section-marker')?.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                  }});
                }}
                
                const sbAts = parentDoc.getElementById('sb-ats');
                if (sbAts && !sbAts.dataset.navSetup) {{
                  sbAts.dataset.navSetup = "true";
                  sbAts.addEventListener('click', () => {{
                    const btn = parentDoc.querySelector('#btn-copilot-trigger-wrapper button');
                    if (btn) btn.click();
                  }});
                }}
    
                // Action triggers for hidden wizard button
                const wizardTriggerFiles = [
                  parentDoc.getElementById('sb-import'),
                  parentDoc.getElementById('sb-settings'),
                  parentDoc.getElementById('mob-fab-trigger')
                ];
                wizardTriggerFiles.forEach(el => {{
                  if (el && !el.dataset.clickSetup) {{
                    el.dataset.clickSetup = "true";
                    el.addEventListener('click', () => {{
                      const btn = parentDoc.querySelector('#btn-dashed-create-arrow-wrapper button');
                      if (btn) btn.click();
                    }});
                  }}
                }});
    
                // Popular template card clicks
                templates.forEach(t => {{
                  const card = parentDoc.getElementById('tpl-' + t);
                  if (card && !card.dataset.clickSetup) {{
                    card.dataset.clickSetup = "true";
                    card.addEventListener('click', () => {{
                      const btn = parentDoc.querySelector('#btn-dashed-create-arrow-wrapper button');
                      if (btn) btn.click();
                    }});
                  }}
                }});
 
                // Mobile bottom navigation click setup
                const mobHome = parentDoc.getElementById('mob-nav-home');
                if (mobHome && !mobHome.dataset.clickSetup) {{
                  mobHome.dataset.clickSetup = "true";
                  mobHome.addEventListener('click', () => {{
                    parentDoc.querySelector('.main .block-container')?.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                    updateActiveMobileNav('mob-nav-home');
                  }});
                }}
 
                const mobTemplates = parentDoc.getElementById('mob-nav-templates');
                if (mobTemplates && !mobTemplates.dataset.clickSetup) {{
                  mobTemplates.dataset.clickSetup = "true";
                  mobTemplates.addEventListener('click', () => {{
                    parentDoc.querySelector('.template-section-marker')?.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                    updateActiveMobileNav('mob-nav-templates');
                  }});
                }}
 
                const mobResumes = parentDoc.getElementById('mob-nav-resumes');
                if (mobResumes && !mobResumes.dataset.clickSetup) {{
                  mobResumes.dataset.clickSetup = "true";
                  mobResumes.addEventListener('click', () => {{
                    parentDoc.querySelector('.mob-resumes-section-marker')?.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                    updateActiveMobileNav('mob-nav-resumes');
                  }});
                }}
 
                const mobProfile = parentDoc.getElementById('mob-nav-profile');
                if (mobProfile && !mobProfile.dataset.clickSetup) {{
                  mobProfile.dataset.clickSetup = "true";
                  mobProfile.addEventListener('click', () => {{
                    parentDoc.querySelector('#mobile-stats-marker')?.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                    updateActiveMobileNav('mob-nav-profile');
                  }});
                }}
 
                function updateActiveMobileNav(activeId) {{
                  const items = ['mob-nav-home', 'mob-nav-templates', 'mob-nav-resumes', 'mob-nav-profile'];
                  items.forEach(id => {{
                    const el = parentDoc.getElementById(id);
                    if (el) {{
                      el.classList.toggle('active', id === activeId);
                    }}
                  }});
                }}
 
                // Scroll spy for mobile navigation
                if (!window.mobScrollSpyRegistered) {{
                  window.mobScrollSpyRegistered = true;
                  let scrollTimeout;
                  parentDoc.addEventListener('scroll', () => {{
                    clearTimeout(scrollTimeout);
                    scrollTimeout = setTimeout(() => {{
                      if (window.parent.innerWidth < 768 || window.innerWidth < 768) {{
                        const resumesMarker = parentDoc.querySelector('.mob-resumes-section-marker');
                        const templatesMarker = parentDoc.querySelector('.mob-section-header-row');
                        const statsMarker = parentDoc.querySelector('#mobile-stats-marker');
                        
                        let activeTab = 'mob-nav-home';
                        
                        if (statsMarker && statsMarker.getBoundingClientRect().top < 200) {{
                          activeTab = 'mob-nav-profile';
                        }} else if (resumesMarker && resumesMarker.getBoundingClientRect().top < 200) {{
                          activeTab = 'mob-nav-resumes';
                        }} else if (templatesMarker && templatesMarker.getBoundingClientRect().top < 200) {{
                          activeTab = 'mob-nav-templates';
                        }}
                        
                        updateActiveMobileNav(activeTab);
                      }}
                    }}, 100);
                  }});
                }}
              }}
    
              setupNavigation();
              const observer = new MutationObserver(() => {{ setupNavigation(); }});
              observer.observe(parentDoc.body, {{ childList: true, subtree: true }});
            }})();
            </script>
            """
        ),
        unsafe_allow_html=True
    )

