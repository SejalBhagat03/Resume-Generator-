import streamlit as st
from resume_builder.services.ai import calculate_health_score
from resume_builder.utils.helpers import clean_html

def get_dynamic_score_data():
    """Calculates active resume score and corresponding status label."""
    try:
        resume_data = st.session_state.get("resume", {})
        hs = calculate_health_score(resume_data)
        score = hs.get("score", 90)
    except Exception:
        score = 90
    
    if score >= 90:
        desc = "Excellent"
    elif score >= 75:
        desc = "Good"
    else:
        desc = "Needs Work"
    return score, desc

def render_hero_desktop():
    """Renders the desktop hero section."""
    score, desc = get_dynamic_score_data()
    st.markdown('<div id="hero-marker"></div>', unsafe_allow_html=True)
    h_col1, h_col2 = st.columns([1.25, 0.75])
    with h_col1:
        st.markdown('<div class="hero-greeting">Welcome back, Sejal! 👋</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-headline">Build Professional,<br><span class="hero-highlight">ATS-Friendly</span> Resumes</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-subtext">Create, customize and export resumes that get you hired.</div>', unsafe_allow_html=True)
        
        # Primary & Secondary action row
        btn_col1, btn_col2 = st.columns([1.1, 1])
        with btn_col1:
            if st.button("＋ Create New Resume", key="hero_create_btn", use_container_width=True):
                st.session_state.wizard_just_opened = True
                st.session_state.show_create_dialog = True
                st.rerun()
        with btn_col2:
            if st.button("📥 Import Resume", key="hero_import_btn", use_container_width=True):
                st.session_state.wizard_just_opened = True
                st.session_state.wizard_import_source = "Existing Resume"
                st.session_state.show_create_dialog = True
                st.rerun()
            
    with h_col2:
        st.markdown(
            clean_html(
                f"""
                <div class="hero-resume-illustration">
                  <div class="illus-avatar"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="8" r="4" fill="#A47148"/><path d="M4 20c0-4 3.582-7 8-7s8 3 8 7" stroke="#A47148" stroke-width="2" stroke-linecap="round"/></svg></div>
                  <div class="illus-title">SUMMARY</div>
                  <div class="illus-line short"></div>
                  <div class="illus-line"></div>
                  <div class="illus-title">EXPERIENCE</div>
                  <div class="illus-line"></div>
                  <div class="illus-line short"></div>
                  
                  <!-- Circular Progress Score Badge (Desktop) -->
                  <div class="illus-score-badge">
                    <div class="score-circle-container">
                      <svg class="score-circle-svg" width="48" height="48" viewBox="0 0 36 36">
                        <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#F1F5F9" stroke-width="3.2" />
                        <path class="circle" stroke-dasharray="{score}, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#10B981" stroke-width="3.2" stroke-linecap="round" />
                      </svg>
                      <div class="score-circle-text">{score}</div>
                    </div>
                    <div class="score-label-container">
                      <span class="score-label-title">ATS Score</span>
                      <span class="score-label-sub">{desc}</span>
                    </div>
                  </div>
                </div>
                """
            ),
            unsafe_allow_html=True
        )

def render_hero_mobile():
    """Renders the mobile hero section."""
    score, desc = get_dynamic_score_data()
    st.markdown('<div id="mob-hero-marker"></div>', unsafe_allow_html=True)
    st.markdown(
        clean_html(
            f"""
            <div class="mob-hero-card">
              <div class="mob-hero-text">
                <div class="mob-hero-greeting">Good Afternoon, Sejal 👋</div>
                <h1 class="mob-hero-title">Build Resumes that<br>Get You Hired</h1>
                <p class="mob-hero-subtitle">Create ATS-friendly resumes, optimize your profile and land your dream job.</p>
                <div class="mob-hero-actions-placeholder"></div>
              </div>
              <div class="mob-hero-illustration">
                <div class="mob-illus-resume">
                  <div class="mob-illus-avatar"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="8" r="4" fill="#A47148"/><path d="M4 20c0-4 3.582-7 8-7s8 3 8 7" stroke="#A47148" stroke-width="2" stroke-linecap="round"/></svg></div>
                  <div class="mob-illus-title">SUMMARY</div>
                  <div class="mob-illus-line short"></div>
                  <div class="mob-illus-line"></div>
                  <div class="mob-illus-title">EXPERIENCE</div>
                  <div class="mob-illus-line"></div>
                  <div class="mob-illus-line short"></div>
                  
                  <!-- Circular Progress Score Badge (Mobile) -->
                  <div class="mob-illus-score-badge">
                    <div class="mob-score-circle-container">
                      <svg class="mob-score-circle-svg" width="38" height="38" viewBox="0 0 36 36">
                        <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#F1F5F9" stroke-width="3.6" />
                        <path class="circle" stroke-dasharray="{score}, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#10B981" stroke-width="3.6" stroke-linecap="round" />
                      </svg>
                      <div class="mob-score-circle-text">{score}</div>
                    </div>
                    <div class="mob-score-label-container">
                      <span class="mob-score-label-title">ATS Score</span>
                      <span class="mob-score-label-sub">{desc}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            """
        ),
        unsafe_allow_html=True
    )

    mob_h_col1, mob_h_col2 = st.columns([1, 1])
    with mob_h_col1:
        if st.button("＋ Create Resume", key="mob_hero_create_btn", use_container_width=True):
            st.session_state.wizard_just_opened = True
            st.session_state.show_create_dialog = True
            st.rerun()
    with mob_h_col2:
        if st.button("📤 Import Resume", key="mob_hero_import_btn", use_container_width=True):
            st.session_state.wizard_just_opened = True
            st.session_state.wizard_import_source = "Existing Resume"
            st.session_state.show_create_dialog = True
            st.rerun()

def render_hero():
    """Compatibility wrapper that routes layout rendering dynamically."""
    if st.session_state.get("is_mobile", False):
        render_hero_mobile()
    else:
        render_hero_desktop()



