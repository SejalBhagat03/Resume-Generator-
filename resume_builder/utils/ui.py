import streamlit as st

def open_card(css_class="card"):
    """Starts a custom HTML card wrapper."""
    st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)

def close_card():
    """Closes a custom HTML card wrapper."""
    st.markdown('</div>', unsafe_allow_html=True)

def render_badge(text, css_class="badge"):
    """Renders a custom HTML badge/pill."""
    st.markdown(f'<span class="{css_class}">{text}</span>', unsafe_allow_html=True)

def render_section_title(title, subtitle=None):
    """Renders a standard section title."""
    html = f'<h2 class="section-title">{title}</h2>'
    if subtitle:
        html += f'<p class="section-subtitle">{subtitle}</p>'
    st.markdown(html, unsafe_allow_html=True)
