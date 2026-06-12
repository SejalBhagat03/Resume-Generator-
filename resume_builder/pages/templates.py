import streamlit as st
from resume_builder.services.storage import save_to_disk

def render_templates_gallery(TID: str):
    """Render the templates design theme visual selector gallery."""
    st.markdown('<div class="sec-title">Select Design Theme</div>', unsafe_allow_html=True)
    st.caption("Choose a curated template style. The live preview updates instantly.")

    TPL_INFOS = {
        "sejal_original": {"name": "Modern Accent", "desc": "Clean typography with subtle color accents.", "icon": "&#x1F3A8;", "color": "#A86A3D"},
        "ats":            {"name": "ATS Professional", "desc": "Industry-standard, highly scannable layout.", "icon": "&#x1F4BC;", "color": "#1E293B"},
        "modern":         {"name": "Elegant Modern", "desc": "Stylish sans-serif theme with modern headings.", "icon": "&#x2728;", "color": "#0F766E"},
        "creative":       {"name": "Creative Bold", "desc": "Vibrant design to stand out in creative roles.", "icon": "&#x1F680;", "color": "#E11D48"},
        "minimal":        {"name": "Minimalist Clean", "desc": "Simple, elegant spacing focusing on content.", "icon": "&#x1F4C4;", "color": "#475569"},
        "two_column":     {"name": "Two Column Splitted", "desc": "Balanced two-column split layout.", "icon": "&#x1F4CA;", "color": "#854D0E"}
    }

    g_cols = st.columns(3, gap="small")
    for i, (tpl_id, info) in enumerate(TPL_INFOS.items()):
        col = g_cols[i % 3]
        with col:
            is_selected = (TID == tpl_id)
            border_css = f"border: 2px solid {info['color'] if is_selected else '#E2E8F0'};"
            bg_css = f"background: {info['color']}08;" if is_selected else "background: #FFFFFF;"
            shadow_css = "box-shadow: 0 4px 12px rgba(168,106,61,0.12);" if is_selected else "box-shadow: 0 1px 3px rgba(0,0,0,0.02);"
            
            st.markdown(
                f'<div style="{border_css} {bg_css} {shadow_css} border-radius: 12px; padding: 12px; height: 180px; display: flex; flex-direction: column; justify-content: space-between; transition: all 0.2s ease;">'
                f'  <div>'
                f'    <div style="display: flex; align-items: center; gap: 8px;">'
                f'      <span style="font-size: 1.4rem;">{info["icon"]}</span>'
                f'      <span style="font-weight: 700; font-size: 0.85rem; color: #1E293B;">{info["name"]}</span>'
                f'    </div>'
                f'    <p style="font-size: 0.72rem; color: #64748B; margin-top: 6px; line-height: 1.3;">{info["desc"]}</p>'
                f'  </div>'
                f'  <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; height: 65px; padding: 6px; display: flex; flex-direction: column; gap: 4px;">'
                f'    <div style="height: 5px; width: 25px; background: {info["color"]}; border-radius: 1px;"></div>'
                f'    <div style="height: 2px; width: 100%; background: #E2E8F0; border-radius: 0.5px;"></div>'
                f'    <div style="display: flex; gap: 4px;">'
                f'      <div style="height: 35px; width: {"50%" if tpl_id == "two_column" else "100%"}; background: white; border: 0.5px solid #E2E8F0; border-radius: 2px; padding: 3px; display: flex; flex-direction: column; gap: 2.5px;">'
                f'        <div style="height: 2px; width: 80%; background: #F1F5F9;"></div>'
                f'        <div style="height: 1.5px; width: 90%; background: #F8FAFC;"></div>'
                f'        <div style="height: 1.5px; width: 70%; background: #F8FAFC;"></div>'
                f'      </div>'
                f'      {"<div style=\'height: 35px; width: 50%; background: white; border: 0.5px solid #E2E8F0; border-radius: 2px; padding: 3px; display: flex; flex-direction: column; gap: 2.5px;\'><div style=\'height: 2px; width: 70%; background: #F1F5F9;\'></div></div>" if tpl_id == "two_column" else ""}'
                f'    </div>'
                f'  </div>'
                f'</div>',
                unsafe_allow_html=True
            )
            btn_txt = "Active Theme" if is_selected else "Select"
            if st.button(btn_txt, key=f"select_tpl_{tpl_id}", type="primary" if is_selected else "secondary", use_container_width=True):
                st.session_state.template = tpl_id
                st.session_state.last_hash = ""
                save_to_disk(st.session_state.resume)
                st.rerun()
