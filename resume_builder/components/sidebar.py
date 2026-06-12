import streamlit as st

def render_sidebar():
    """Renders the side navigation drawer."""
    sidebar_html = """
    <div class="rb-overlay" id="rb-overlay"></div>

    <div class="rb-sidebar" id="rb-sidebar">
      <button class="rb-sidebar-item active" id="sb-home">
        <span class="rb-sidebar-icon">&#x1F3E0;</span>
        <span class="rb-sidebar-label">Home</span>
      </button>
      <button class="rb-sidebar-item" id="sb-templates">
        <span class="rb-sidebar-icon">&#x1F4C4;</span>
        <span class="rb-sidebar-label">Templates</span>
      </button>
      <button class="rb-sidebar-item" id="sb-resumes">
        <span class="rb-sidebar-icon">&#128194;</span>
        <span class="rb-sidebar-label">Resumes</span>
      </button>
      <button class="rb-sidebar-item" id="sb-profile">
        <span class="rb-sidebar-icon">&#x1F464;</span>
        <span class="rb-sidebar-label">Profile</span>
      </button>
    </div>
    """
    st.markdown(sidebar_html, unsafe_allow_html=True)
