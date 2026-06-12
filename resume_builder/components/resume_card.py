import streamlit as st
from resume_builder.utils.helpers import clean_html
import html
import os

def render_resume_grid_card(r, tpl_disp, rel_time):
    """Renders a single resume card in the grid on desktop."""
    # Compute active template layout colors/thumbnails
    color = r.get("color", "#A86A3D")
    
    st.markdown(
        clean_html(
            f"""
            <div class="resume-grid-card">
                <div class="resume-grid-thumb">
                    <!-- Mini simulated page preview -->
                    <div class="mini-resume-page">
                        <div class="mini-header" style="border-top: 4px solid {color};">
                            <div class="mini-dot"></div>
                            <div class="mini-line-short"></div>
                        </div>
                        <div class="mini-body">
                            <div class="mini-line"></div>
                            <div class="mini-line-short"></div>
                            <div class="mini-line"></div>
                        </div>
                    </div>
                </div>
                <div class="resume-grid-info">
                    <div class="resume-grid-title">{html.escape(r["title"])}</div>
                    <div class="resume-grid-badge-row">
                        <span class="theme-badge">{tpl_disp}</span>
                    </div>
                    <div class="resume-grid-date">Updated {rel_time}</div>
                </div>
            </div>
            """
        ),
        unsafe_allow_html=True
    )

def render_continue_card_desktop(latest_resume, tpl_disp, rel_time, mod_date):
    """Renders the desktop 'Continue Editing' card (left side info)."""
    color = latest_resume.get("color", "#A86A3D")
    st.markdown(
        clean_html(
            f"""
            <div class="continue-card-content">
                <div class="continue-card-thumb">
                    <!-- Mini simulated page preview -->
                    <div class="mini-resume-page-flat">
                        <div class="mini-flat-header" style="background: {color};"></div>
                        <div class="mini-flat-body">
                            <div class="mini-flat-line"></div>
                            <div class="mini-flat-line-short"></div>
                        </div>
                    </div>
                </div>
                <div class="continue-card-info">
                    <div class="continue-card-title">{html.escape(latest_resume["title"])}</div>
                    <div class="continue-card-meta-row">
                        <span class="theme-badge">{tpl_disp}</span>
                        <span class="continue-card-time">Last edited {rel_time} &bull; Updated on {mod_date}</span>
                    </div>
                </div>
            </div>
            """
        ),
        unsafe_allow_html=True
    )

def render_continue_card_mobile(latest_resume, tpl_disp, rel_time):
    """Renders the mobile 'Continue Editing' card (left side info)."""
    color = latest_resume.get("color", "#A86A3D")
    st.markdown(
        clean_html(
            f"""
            <div class="mob-continue-card">
                <div class="mob-continue-left">
                    <div class="mob-continue-thumb">
                        <!-- Mini simulated flat page -->
                        <div class="mini-resume-page-flat-mob">
                            <div class="mini-flat-header-mob" style="background: {color};"></div>
                            <div class="mini-flat-body-mob">
                                <div class="mini-flat-line-mob"></div>
                            </div>
                        </div>
                    </div>
                    <div class="mob-continue-info">
                        <div class="mob-continue-title">{html.escape(latest_resume["title"])}</div>
                        <div class="mob-continue-meta">
                            <span class="mob-continue-badge">{tpl_disp}</span>
                            <span class="mob-continue-time">Edited {rel_time}</span>
                        </div>
                    </div>
                </div>
            </div>
            """
        ),
        unsafe_allow_html=True
    )

