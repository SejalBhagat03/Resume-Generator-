import streamlit as st
from resume_builder.utils.helpers import clean_html

def render_navbar():
    """Renders the top navigation bar."""
    navbar_html = """
    <div class="rb-main-header">
      <!-- Left side: hamburger menu & logo (mobile only) -->
      <div class="rb-header-left">
        <div class="rb-hamburger" id="rb-hamburger">&#9776;</div>
        <div class="rb-logo">
          <span><svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z" fill="#A47148"/></svg></span>
          <span class="rb-logo-text">Resume Builder Pro</span>
        </div>
      </div>
      
      <!-- Right side: notifications, avatar -->
      <div class="rb-header-right">
        <div class="rb-noti">
          &#128276;
          <span class="rb-noti-badge"></span>
        </div>
        <div class="rb-avatar">SB</div>
        <span class="rb-avatar-chevron">▼</span>
      </div>
    </div>
    """
    st.markdown(clean_html(navbar_html), unsafe_allow_html=True)


