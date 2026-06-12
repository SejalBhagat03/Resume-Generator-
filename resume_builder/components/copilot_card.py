import streamlit as st
from resume_builder.utils.helpers import clean_html

def render_copilot_card():
    """Renders the light-green AI Career Copilot information card."""
    st.markdown('<div id="copilot-card-marker"></div>', unsafe_allow_html=True)
    
    st.markdown(
        clean_html(
            """
            <div class="rb-copilot-card">
              <div class="rb-copilot-left">
                <div class="rb-copilot-icon-circle">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2L14.65 8.65L21 9L16 13.5L17.8 20L12 16L6.2 20L8 13.5L3 9L9.35 8.65L12 2Z" fill="#15803D" stroke="#15803D" stroke-width="2" stroke-linejoin="round"/></svg>
                </div>
                <div class="rb-copilot-info">
                  <div class="rb-copilot-title-row">
                    <span class="rb-copilot-title">AI Career Copilot</span>
                    <span class="rb-copilot-badge">NEW</span>
                  </div>
                  <div class="rb-copilot-desc">Get AI-powered suggestions to improve your resume and increase interview calls.</div>
                </div>
              </div>
              <div class="rb-copilot-right">
                <button class="rb-copilot-btn" id="btn-copilot-view">View Suggestions &rsaquo;</button>
              </div>
            </div>
            """
        ),
        unsafe_allow_html=True
    )

    
    # Hidden Streamlit action button
    st.markdown('<div id="btn-copilot-trigger-wrapper" style="display:none;">', unsafe_allow_html=True)
    if st.button("", key="btn_copilot_trigger"):
        # Switch to the first resume (active resume) and open the ATS/Review tab
        resumes = st.session_state.get("resumes_list", [])
        if resumes:
            from resume_builder.services.storage import load_active_resume
            load_active_resume(resumes[0]["path"])
            st.session_state.navigation_page = "workspace"
            st.session_state.editor_step = 5  # Index for Review / Insights tab
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
