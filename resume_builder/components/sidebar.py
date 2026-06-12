import streamlit as st
from resume_builder.utils.helpers import clean_html

def render_sidebar():
    """Renders the side navigation drawer."""
    sidebar_html = """
    <div class="rb-overlay" id="rb-overlay"></div>

    <div class="rb-sidebar" id="rb-sidebar">
      <div class="rb-sidebar-brand">
        <span class="rb-brand-icon"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z" fill="#A47148"/></svg></span>
        <span class="rb-brand-text">Resume Builder Pro</span>
      </div>

      <div class="rb-sidebar-menu">
        <button class="rb-sidebar-item active" id="sb-home">
          <span class="rb-sidebar-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
          </span>
          <span class="rb-sidebar-label">Dashboard</span>
        </button>
        <button class="rb-sidebar-item" id="sb-resumes">
          <span class="rb-sidebar-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/></svg>
          </span>
          <span class="rb-sidebar-label">My Resumes</span>
        </button>
        <button class="rb-sidebar-item" id="sb-templates">
          <span class="rb-sidebar-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/></svg>
          </span>
          <span class="rb-sidebar-label">Templates</span>
        </button>
        <button class="rb-sidebar-item" id="sb-ats">
          <span class="rb-sidebar-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
          </span>
          <span class="rb-sidebar-label">ATS Analysis</span>
        </button>
        <button class="rb-sidebar-item" id="sb-import">
          <span class="rb-sidebar-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
          </span>
          <span class="rb-sidebar-label">Import Resume</span>
        </button>
        
        <div class="rb-sidebar-divider"></div>
        
        <button class="rb-sidebar-item" id="sb-settings">
          <span class="rb-sidebar-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
          </span>
          <span class="rb-sidebar-label">Settings</span>
        </button>
        <button class="rb-sidebar-item" id="sb-help">
          <span class="rb-sidebar-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          </span>
          <span class="rb-sidebar-label">Help & Support</span>
        </button>
      </div>

      <div class="rb-upgrade-card">
        <div class="rb-upgrade-crown">👑</div>
        <div class="rb-upgrade-title">Upgrade to Pro</div>
        <div class="rb-upgrade-desc">Unlock premium templates, ATS score and more features.</div>
        <button class="rb-upgrade-btn" id="sb-upgrade-trigger">Upgrade Now</button>
      </div>

      <div class="rb-user-profile" id="sb-profile-menu">
        <div class="rb-profile-avatar">SB</div>
        <div class="rb-profile-info">
          <div class="rb-profile-name">Sejal B.</div>
          <div class="rb-profile-plan">Free Plan</div>
        </div>
        <span class="rb-profile-chevron">▼</span>
      </div>
    </div>
    """
    st.markdown(clean_html(sidebar_html), unsafe_allow_html=True)



