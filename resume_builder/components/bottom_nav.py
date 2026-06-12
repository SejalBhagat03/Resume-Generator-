import streamlit as st
from resume_builder.utils.helpers import clean_html

def render_bottom_nav():
    """Renders the mobile bottom navigation bar."""
    st.markdown(
        clean_html(
            """
            <div class="mob-bottom-nav">
              <div class="mob-nav-item active" id="mob-nav-home">
                <span class="mob-nav-icon">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
                </span>
                <span class="mob-nav-label">Home</span>
              </div>
              <div class="mob-nav-item" id="mob-nav-templates">
                <span class="mob-nav-icon">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/></svg>
                </span>
                <span class="mob-nav-label">Templates</span>
              </div>
              <div class="mob-nav-item" id="mob-nav-resumes">
                <span class="mob-nav-icon">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/></svg>
                </span>
                <span class="mob-nav-label">Resumes</span>
              </div>
              <div class="mob-nav-item" id="mob-nav-profile">
                <span class="mob-nav-icon">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                </span>
                <span class="mob-nav-label">Profile</span>
              </div>
            </div>
            """
        ),
        unsafe_allow_html=True
    )

