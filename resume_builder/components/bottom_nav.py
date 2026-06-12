import streamlit as st

def render_bottom_nav():
    """Renders the mobile bottom navigation bar and hidden Streamlit button triggers."""
    # Bottom Navigation Bar Sticky using marker and columns (hidden on desktop, active on mobile)
    st.markdown("<div id='bottom-nav-marker'></div>", unsafe_allow_html=True)
    b_col1, b_col2, b_col3, b_col4 = st.columns(4)
    with b_col1:
        st.button("&#x1F3E0;\nHome", key="nav_home_btn", use_container_width=True)
    with b_col2:
        st.button("&#x1F4C4;\nTemplates", key="nav_templates_btn", use_container_width=True)
    with b_col3:
        st.button("&#128194;\nResumes", key="nav_resumes_btn", use_container_width=True)
    with b_col4:
        st.button("&#x1F464;\nProfile", key="nav_profile_btn", use_container_width=True)

    # Bottom Navigation (Mobile Only HTML)
    st.markdown(
        """
        <div class="mob-bottom-nav">
          <div class="mob-nav-item active" id="mob-nav-home">
            <span class="mob-nav-icon">&#x1F3E0;</span>
            <span class="mob-nav-label">Home</span>
          </div>
          <div class="mob-nav-item" id="mob-nav-templates">
            <span class="mob-nav-icon">&#x1F4C4;</span>
            <span class="mob-nav-label">Templates</span>
          </div>
          <div class="mob-nav-item" id="mob-nav-resumes">
            <span class="mob-nav-icon">&#128194;</span>
            <span class="mob-nav-label">Resumes</span>
          </div>
          <div class="mob-nav-item" id="mob-nav-profile">
            <span class="mob-nav-icon">&#x1F464;</span>
            <span class="mob-nav-label">Profile</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )
