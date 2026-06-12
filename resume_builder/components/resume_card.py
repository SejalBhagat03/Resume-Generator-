import streamlit as st
import html

def render_resume_grid_card(r, tpl_disp, rel_time):
    """Renders a single resume card in the grid."""
    st.markdown(
        f"""
        <div class="resume-grid-card">
            <div class="resume-grid-thumb">
                <div style="font-size: 2.5rem; display: flex; align-items: center; justify-content: center; height: 100%;">&#x1F4C4;</div>
            </div>
            <div class="resume-grid-info">
                <div class="resume-grid-title">{html.escape(r["title"])}</div>
                <div class="resume-grid-badge-row">
                    <span class="theme-badge">{tpl_disp}</span>
                </div>
                <div class="resume-grid-date">Updated {rel_time}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_continue_card_desktop(latest_resume, tpl_disp, rel_time):
    """Renders the desktop 'Continue Editing' card."""
    st.markdown(
        f"""
        <div class="continue-card-content">
            <div class="continue-card-thumb">
                <div style="font-size: 2.2rem; display: flex; align-items: center; justify-content: center; height: 100%;">&#x1F4C4;</div>
            </div>
            <div class="continue-card-info">
                <div class="continue-card-title">{html.escape(latest_resume["title"])}</div>
                <div>
                    <span class="theme-badge">{tpl_disp}</span>
                    <span class="continue-card-time">Edited {rel_time}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_continue_card_mobile(latest_resume, tpl_disp, rel_time):
    """Renders the mobile 'Continue Editing' card."""
    st.markdown(
        f"""
        <div class="mob-continue-card">
            <div class="mob-continue-left">
                <div class="mob-continue-thumb">&#x1F4C4;</div>
                <div class="mob-continue-info">
                    <div class="mob-continue-title">{html.escape(latest_resume["title"])}</div>
                    <div class="mob-continue-meta">
                        <span class="mob-continue-badge">{tpl_disp}</span>
                        <span class="mob-continue-time">Edited {rel_time}</span>
                    </div>
                </div>
            </div>
            <div class="mob-continue-right-placeholder"></div>
        </div>
        """,
        unsafe_allow_html=True
    )
