import streamlit as st

def render_search_bar_desktop(search_query: str):
    """Renders the desktop search and filter section."""
    st.markdown("<div id='search-section-marker'></div>", unsafe_allow_html=True)
    st.markdown("<div class='search-row-container'>", unsafe_allow_html=True)
    col_s1, col_s2 = st.columns([4.2, 0.8])
    with col_s1:
        st.markdown("<div class='search-input-box'>", unsafe_allow_html=True)
        st.text_input(
            "Search resumes",
            value=search_query,
            placeholder="Search resumes...",
            label_visibility="collapsed",
            key="search_resumes_val"
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with col_s2:
        st.markdown("<div class='filter-btn-box'>", unsafe_allow_html=True)
        st.button("&#127899;&#65039;", key="home_filter_btn", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def render_search_bar_mobile(search_query: str):
    """Renders the mobile search and filter section."""
    st.markdown('<div id="mob-search-marker"></div>', unsafe_allow_html=True)
    st.markdown("<div class='mob-search-row-container'>", unsafe_allow_html=True)
    mob_col_s1, mob_col_s2 = st.columns([4.2, 0.8])
    with mob_col_s1:
        st.markdown("<div class='mob-search-input-box'>", unsafe_allow_html=True)
        st.text_input(
            "Search resumes mobile",
            value=search_query,
            placeholder="Search your resumes...",
            label_visibility="collapsed",
            key="mob_search_resumes_val"
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with mob_col_s2:
        st.markdown("<div class='mob-filter-btn-box'>", unsafe_allow_html=True)
        st.button("&#127899;&#65039;", key="mob_filter_btn", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
