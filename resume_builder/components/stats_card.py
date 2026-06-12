import streamlit as st

def kpi_card_html(label: str, value: str, hint: str, color: str) -> str:
    """Returns the HTML string for an enhanced KPI card."""
    return (
        f'<div class="kpi-enhanced {color}">'
        f'<div class="kpi-lbl2">{label}</div>'
        f'<div class="kpi-val2 {color}">{value}</div>'
        f'<div class="kpi-hint2">{hint}</div>'
        f'</div>'
    )

def render_kpi_card(label: str, value: str, hint: str, color: str):
    """Renders an enhanced KPI card directly in Streamlit."""
    st.markdown(kpi_card_html(label, value, hint, color), unsafe_allow_html=True)
