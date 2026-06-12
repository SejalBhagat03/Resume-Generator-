import streamlit as st
from typing import List
from resume_builder.utils.helpers import clean_html

def render_stepper(current_step: int, steps: List[str]):
    """Render a horizontal stepper with circles.

    Args:
        current_step: Zero‑based index of the step currently being displayed.
        steps: List of step titles (e.g. ["Personal", "Experience", "Design"]).
    """
    # Use Streamlit columns to lay out circles and connecting lines
    cols = st.columns([1] * len(steps))
    for idx, (col, title) in enumerate(zip(cols, steps)):
        is_completed = idx < current_step
        is_current = idx == current_step
        # Colors from the new palette
        circle_bg = "#8B5E3C" if is_completed or is_current else "#EFE7DD"
        border = "#8B5E3C" if is_current else "#D6C5B4"
        size = 44 if is_current else 36
        with col:
            # Circle
            st.markdown(
                clean_html(
                    f"""
                    <div style="
                        width:{size}px;
                        height:{size}px;
                        line-height:{size}px;
                        border:{'2px' if is_current else '1px'} solid {border};
                        border-radius:50%;
                        background:{circle_bg};
                        color:#fff;
                        font-weight:600;
                        text-align:center;
                        margin:auto;
                    ">{idx + 1}</div>
                    <div style="text-align:center;font-size:0.75rem;color:#2C2C2C;margin-top:4px;">{title}</div>
                    """
                ),
                unsafe_allow_html=True,
            )
            # Connecting line (except after the last step)
            if idx < len(steps) - 1:
                st.markdown(
                    "<div style='height:2px;background:#8B5E3C;margin:4px auto;width:100%;'></div>",
                    unsafe_allow_html=True,
                )

