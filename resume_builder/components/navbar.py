import streamlit as st

def render_navbar():
    """Renders the top navigation bar."""
    # We will use st.markdown to render the custom HTML.
    # Note: the CSS for these classes should be in assets/components.css or layout.css
    navbar_html = """
    <div class="rb-main-header">
      <div class="rb-header-left">
        <div class="rb-hamburger" id="rb-hamburger">&#9776;</div>
        <div class="rb-logo">
          <span>&#x1F4C4;</span>
          <span class="rb-logo-text">Resume Builder Pro</span>
        </div>
      </div>
      <div class="rb-header-right">
        <div class="rb-noti">&#128276;</div>
        <div class="rb-avatar">S</div>
      </div>
    </div>
    """
    st.markdown(navbar_html, unsafe_allow_html=True)
