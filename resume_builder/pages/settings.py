import streamlit as st
from resume_builder.utils.helpers import margin_label, fscale_label

def render_layout_settings(M: int, FS: float, FT: str):
    """Render sliders for margin, font scale, and fitting radio options."""
    st.markdown('<div class="sec-title">Page Layout Settings</div>', unsafe_allow_html=True)
    
    new_m = st.slider("Margin (pt)", 10, 36, M, 2, key="adv_mg")
    m_txt, m_cls = margin_label(new_m)
    st.markdown(f'Current: <b>{new_m}pt</b> &rarr; <span class="setting-effect {m_cls}">{m_txt}</span>', unsafe_allow_html=True)
    
    new_fs = st.slider("Font Scale", 0.75, 1.25, FS, 0.05, key="adv_fs")
    fs_txt, fs_cls = fscale_label(new_fs)
    st.markdown(f'Current: <b>{new_fs:.2f}×</b> &rarr; <span class="setting-effect {fs_cls}">{fs_txt}</span>', unsafe_allow_html=True)
    
    FITTING_OPTS = ["Auto Compress", "Keep Original", "Multi-Page"]
    new_ft = st.radio("Page Fitting", FITTING_OPTS, index=FITTING_OPTS.index(FT), key="adv_fit", horizontal=True)
    
    return new_m, new_fs, new_ft
