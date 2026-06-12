import streamlit as st

def render_hero():
    """Renders the desktop and mobile hero sections."""
    # 3. Hero Section (Desktop)
    st.markdown('<div id="hero-marker"></div>', unsafe_allow_html=True)
    h_col1, h_col2 = st.columns([1, 1])
    with h_col1:
        st.markdown('<div class="hero-headline">Create Professional,<br><span class="hero-highlight">ATS-Friendly</span> Resumes</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-subtext">Build, customize and export resumes that help you get hired.</div>', unsafe_allow_html=True)
        
        # Primary Action
        if st.button("&#x2795; Create Resume", key="hero_create_btn", use_container_width=True):
            st.session_state.wizard_just_opened = True
            st.session_state.show_create_dialog = True
            st.rerun()
            
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        
        # Secondary Action
        if st.button("&#x1F4E5; Import Resume", key="hero_import_btn", use_container_width=True):
            st.session_state.wizard_just_opened = True
            st.session_state.wizard_import_source = "Existing Resume"
            st.session_state.show_create_dialog = True
            st.rerun()
            
    with h_col2:
        st.markdown(
            """
            <div class="hero-resume-illustration">
              <div class="illus-avatar"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="8" r="4" fill="#A47148"/><path d="M4 20c0-4 3.582-7 8-7s8 3 8 7" stroke="#A47148" stroke-width="2" stroke-linecap="round"/></svg></div>
              <div class="illus-title">CONTACTS</div>
              <div class="illus-line short"></div>
              <div class="illus-line"></div>
              <div class="illus-title">EXPERIENCE</div>
              <div class="illus-line"></div>
              <div class="illus-line short"></div>
              <div class="illus-score-badge">
                <div class="score-number">95</div>
                <div class="score-text">ATS Score</div>
                <div class="score-desc">Excellent</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 3. Hero Section (Mobile)
    st.markdown('<div id="mob-hero-marker"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="mob-hero-card">
          <div class="mob-hero-text">
            <h1 class="mob-hero-title">Create Professional ATS-Friendly Resumes</h1>
            <p class="mob-hero-subtitle">Build resumes that get interviews.</p>
            <div class="mob-hero-actions-placeholder"></div>
          </div>
          <div class="mob-hero-illustration">
            <div class="mob-illus-resume">
              <div class="mob-illus-avatar"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="8" r="4" fill="#A47148"/><path d="M4 20c0-4 3.582-7 8-7s8 3 8 7" stroke="#A47148" stroke-width="2" stroke-linecap="round"/></svg></div>
              <div class="mob-illus-title">CONTACTS</div>
              <div class="mob-illus-line short"></div>
              <div class="mob-illus-line"></div>
              <div class="mob-illus-title">EXPERIENCE</div>
              <div class="mob-illus-line"></div>
              <div class="mob-illus-line short"></div>
              <div class="mob-illus-score-badge">
                <div class="mob-score-number">95</div>
                <div class="mob-score-text">ATS Score</div>
                <div class="mob-score-desc">Excellent</div>
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    mob_h_col1, mob_h_col2 = st.columns([1, 1])
    with mob_h_col1:
        if st.button("&#x2795; Create Resume", key="mob_hero_create_btn", use_container_width=True):
            st.session_state.wizard_just_opened = True
            st.session_state.show_create_dialog = True
            st.rerun()
    with mob_h_col2:
        if st.button("&#x1F4E5; Import Resume", key="mob_hero_import_btn", use_container_width=True):
            st.session_state.wizard_just_opened = True
            st.session_state.wizard_import_source = "Existing Resume"
            st.session_state.show_create_dialog = True
            st.rerun()
