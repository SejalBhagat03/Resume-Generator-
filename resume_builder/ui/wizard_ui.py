import streamlit as st
from typing import List
from resume_builder.templates import TEMPLATES as ALL_TEMPLATES

def clean_html(html: str) -> str:
    """Helper to strip leading whitespace from each line of HTML to prevent Markdown parser code blocks."""
    return "\n".join(line.strip() for line in html.strip().splitlines())

# Helper to render the header of the Create Resume wizard modal
def render_wizard_header(title: str = "Create New Resume", subtitle: str = "Build a professional resume in 3 simple steps"):
    """Renders modal header with icon, title, and subtitle."""
    html = f"""
    <div class="wizard-header">
        <div class="icon">✏️</div>
        <div>
            <div class="wizard-title">{title}</div>
            <div class="wizard-subtitle">{subtitle}</div>
        </div>
    </div>
    """
    st.markdown(clean_html(html), unsafe_allow_html=True)

# Helper to render a circular stepper
def render_wizard_stepper(current_step: int, steps: List[str]):
    """Renders a horizontal stepper with circles and connector lines."""
    steps_html = []
    labels_html = []
    
    for i, step_name in enumerate(steps):
        step_idx = i + 1
        circle_cls = ""
        label_cls = ""
        
        if step_idx == current_step:
            circle_cls = "active"
            label_cls = "active"
        elif step_idx < current_step:
            circle_cls = "completed"
            label_cls = "completed"
            
        steps_html.append(f"<div class='wizard-step {circle_cls}'>{step_idx}</div>")
        
        if i < len(steps) - 1:
            conn_cls = "completed" if step_idx < current_step else ""
            steps_html.append(f"<span class='wizard-stepper-connector {conn_cls}'></span>")
            
        labels_html.append(f"<div class='wizard-stepper-label {label_cls}'>{step_name}</div>")
        
    html = f"""
    <div class="wizard-stepper">
        {"".join(steps_html)}
    </div>
    <div class="wizard-stepper-labels">
        {"".join(labels_html)}
    </div>
    """
    st.markdown(clean_html(html), unsafe_allow_html=True)

# Profile type selection cards (Step 1)
def render_profile_type_cards(selected: str):
    """Displays selectable cards for profile types and updates session state.
    Options: Fresh Graduate, Experienced Professional, Internship Resume, Academic Resume, Custom.
    """
    options = [
        ("🎓", "Fresh Graduate", "Entry-level positions and new graduates"),
        ("💼", "Experienced", "For professionals with experience"),
        ("🚀", "Internship", "Internships & student positions"),
        ("📚", "Academic", "Research & academic careers"),
        ("✏️", "Custom", "Build from scratch"),
    ]
    
    st.markdown("<div id='wizard-cards-marker'></div>", unsafe_allow_html=True)
    cols = st.columns(5)
    
    for idx, (icon, label, desc) in enumerate(options):
        full_label = label
        if label == "Experienced":
            full_label = "Experienced Professional"
        elif label == "Internship":
            full_label = "Internship Resume"
        elif label == "Academic":
            full_label = "Academic Resume"
            
        is_selected = (selected == full_label)
        
        with cols[idx]:
            st.markdown(f"<div style='font-size: 2.2rem; margin-bottom: 6px;'>{icon}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-weight: 700; color: #1E2A44; font-size: 0.95rem; margin-bottom: 4px;'>{label}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size: 0.75rem; color: #64748B; margin-bottom: 12px; height: 38px; overflow: hidden; line-height: 1.3;'>{desc}</div>", unsafe_allow_html=True)
            
            btn_label = "Selected ✓" if is_selected else "Select"
            if st.button(btn_label, key=f"profile_btn_{idx}", use_container_width=True, disabled=is_selected):
                st.session_state.wizard_resume_type = full_label
                st.rerun()

# Import source selection cards (Step 2)
def render_import_cards(selected: str):
    """Displays import source cards and handles state update."""
    options = [
        ("✨", "Start Empty", "Create a brand-new resume"),
        ("📄", "Existing Resume", "Upload an existing file"),
        ("🔗", "LinkedIn PDF", "Import from LinkedIn PDF"),
        ("💻", "GitHub", "Pull projects from GitHub"),
    ]
    
    st.markdown("<div id='wizard-cards-marker'></div>", unsafe_allow_html=True)
    cols = st.columns(4)
    
    for idx, (icon, label, desc) in enumerate(options):
        is_selected = (selected == label)
        
        with cols[idx]:
            st.markdown(f"<div style='font-size: 2.2rem; margin-bottom: 6px;'>{icon}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-weight: 700; color: #1E2A44; font-size: 0.95rem; margin-bottom: 4px;'>{label}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size: 0.75rem; color: #64748B; margin-bottom: 12px; height: 38px; overflow: hidden; line-height: 1.3;'>{desc}</div>", unsafe_allow_html=True)
            
            btn_label = "Selected ✓" if is_selected else "Select"
            if st.button(btn_label, key=f"import_btn_{idx}", use_container_width=True, disabled=is_selected):
                st.session_state.wizard_import_source = label
                st.rerun()
