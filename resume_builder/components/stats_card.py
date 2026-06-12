import streamlit as st
import os
import json
from resume_builder.services.storage import list_resumes
from resume_builder.services.ai import calculate_health_score
from resume_builder.utils.helpers import clean_html

def get_kpi_data():
    """Computes layout KPI stats dynamically from the disk database."""
    resumes = list_resumes()
    num_resumes = len(resumes)
    unique_templates = len(set(r.get("template", "default") for r in resumes)) if resumes else 0
    
    # Calculate average ATS score
    scores = []
    for r in resumes:
        try:
            with open(r["path"], "r", encoding="utf-8") as f:
                data = json.load(f)
            hs = calculate_health_score(data)
            scores.append(hs.get("score", 90))
        except Exception:
            pass
    avg_score = int(sum(scores) / len(scores)) if scores else 90

    # Count PDFs in exports
    try:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        pdf_dir = os.path.join(project_root, "exports", "pdf")
        num_downloads = len([f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]) if os.path.exists(pdf_dir) else 0
    except Exception:
        num_downloads = 0

    return num_resumes, num_downloads, avg_score, unique_templates

def render_desktop_stats():
    """Renders the row of 4 KPI cards on desktop."""
    st.markdown('<div id="desktop-stats-marker"></div>', unsafe_allow_html=True)
    num_resumes, num_downloads, avg_score, unique_templates = get_kpi_data()
    
    col1, col2, col3, col4 = st.columns(4)
    
    # 1. Total Resumes
    with col1:
        st.markdown(
            clean_html(
                f"""
                <div class="rb-kpi-card">
                  <div class="rb-kpi-icon-wrapper">
                    <div class="rb-kpi-icon-circle">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z" fill="#A47148"/></svg>
                    </div>
                  </div>
                  <div class="rb-kpi-content">
                    <div class="rb-kpi-label">Total Resumes</div>
                    <div class="rb-kpi-value">{num_resumes}</div>
                    <div class="rb-kpi-subtext">Resumes created</div>
                  </div>
                </div>
                """
            ),
            unsafe_allow_html=True
        )
        
    # 2. Total Downloads
    with col2:
        st.markdown(
            clean_html(
                f"""
                <div class="rb-kpi-card">
                  <div class="rb-kpi-icon-wrapper">
                    <div class="rb-kpi-icon-circle">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM17 13l-5 5-5-5h3V9h4v4h3z" fill="#A47148"/></svg>
                    </div>
                  </div>
                  <div class="rb-kpi-content">
                    <div class="rb-kpi-label">Total Downloads</div>
                    <div class="rb-kpi-value">{num_downloads}</div>
                    <div class="rb-kpi-subtext">PDF downloads</div>
                  </div>
                </div>
                """
            ),
            unsafe_allow_html=True
        )
        
    # 3. Average ATS Score
    with col3:
        st.markdown(
            clean_html(
                f"""
                <div class="rb-kpi-card">
                  <div class="rb-kpi-icon-wrapper">
                    <div class="rb-kpi-icon-circle">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M16 6l2.29 2.29-4.88 4.88-4-4L2 16.59 3.41 18l6-6 4 4 6.3-6.29L22 12V6h-6z" fill="#A47148"/></svg>
                    </div>
                  </div>
                  <div class="rb-kpi-content">
                    <div class="rb-kpi-label">Average ATS Score</div>
                    <div class="rb-kpi-value">{avg_score}%</div>
                    <div class="rb-kpi-subtext">Across all resumes</div>
                  </div>
                </div>
                """
            ),
            unsafe_allow_html=True
        )
        
    # 4. Templates Used
    with col4:
        st.markdown(
            clean_html(
                f"""
                <div class="rb-kpi-card">
                  <div class="rb-kpi-icon-wrapper">
                    <div class="rb-kpi-icon-circle">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M4 11h5V5H4v6zm0 7h5v-6H4v6zm6 0h5v-6h-5v6zm6 0h5v-6h-5v6zm-6-7h5V5h-5v6zm6-6v6h5V5h-5z" fill="#A47148"/></svg>
                    </div>
                  </div>
                  <div class="rb-kpi-content">
                    <div class="rb-kpi-label">Templates Used</div>
                    <div class="rb-kpi-value">{unique_templates}</div>
                    <div class="rb-kpi-subtext">Different templates</div>
                  </div>
                </div>
                """
            ),
            unsafe_allow_html=True
        )

def render_mobile_stats():
    """Renders the circular progress stats section for mobile."""
    st.markdown('<div id="mobile-stats-marker"></div>', unsafe_allow_html=True)
    
    st.markdown(
        clean_html(
            """
            <div class="mob-section-header-row">
              <span class="mob-section-title">Your Career Progress</span>
              <span class="mob-view-all-link">View Details &rsaquo;</span>
            </div>
            """
        ),
        unsafe_allow_html=True
    )
    
    # Calculate mobile metrics dynamically from active resume
    try:
        resume_data = st.session_state.get("resume", {})
        hs = calculate_health_score(resume_data)
        ats_score = hs.get("score", 90)
    except Exception:
        ats_score = 90

    # Derive profile strength and resume quality from the ATS score
    profile_strength = min(100, max(50, ats_score - 5))
    resume_quality = min(100, max(40, ats_score - 12))

    # Determine status and color classes
    def get_status_data(score, is_strength=False):
        if score >= 85:
            return ("Great" if is_strength else "Excellent"), "green", "#10B981"
        elif score >= 70:
            return "Good", "amber", "#F59E0B"
        else:
            return "Needs Work", "red", "#EF4444"

    ps_lbl, ps_cls, ps_color = get_status_data(profile_strength, is_strength=True)
    rq_lbl, rq_cls, rq_color = get_status_data(resume_quality)
    ats_lbl, ats_cls, ats_color = get_status_data(ats_score)

    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            clean_html(
                f"""
                <div class="rb-progress-card">
                  <div class="rb-progress-circle-wrapper">
                    <svg class="rb-progress-circle-svg" width="60" height="60" viewBox="0 0 36 36">
                      <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#F1F5F9" stroke-width="3.2" />
                      <path class="circle" stroke-dasharray="{profile_strength}, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="{ps_color}" stroke-width="3.2" stroke-linecap="round" />
                    </svg>
                    <div class="rb-progress-percent">{profile_strength}%</div>
                  </div>
                  <div class="rb-progress-info">
                    <div class="rb-progress-label">Profile Strength</div>
                    <div class="rb-progress-status {ps_cls}">{ps_lbl}</div>
                  </div>
                </div>
                """
            ),
            unsafe_allow_html=True
        )
        
    with col2:
        st.markdown(
            clean_html(
                f"""
                <div class="rb-progress-card">
                  <div class="rb-progress-circle-wrapper">
                    <svg class="rb-progress-circle-svg" width="60" height="60" viewBox="0 0 36 36">
                      <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#F1F5F9" stroke-width="3.2" />
                      <path class="circle" stroke-dasharray="{resume_quality}, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="{rq_color}" stroke-width="3.2" stroke-linecap="round" />
                    </svg>
                    <div class="rb-progress-percent">{resume_quality}%</div>
                  </div>
                  <div class="rb-progress-info">
                    <div class="rb-progress-label">Resume Quality</div>
                    <div class="rb-progress-status {rq_cls}">{rq_lbl}</div>
                  </div>
                </div>
                """
            ),
            unsafe_allow_html=True
        )
        
    with col3:
        st.markdown(
            clean_html(
                f"""
                <div class="rb-progress-card">
                  <div class="rb-progress-circle-wrapper">
                    <svg class="rb-progress-circle-svg" width="60" height="60" viewBox="0 0 36 36">
                      <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#F1F5F9" stroke-width="3.2" />
                      <path class="circle" stroke-dasharray="{ats_score}, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="{ats_color}" stroke-width="3.2" stroke-linecap="round" />
                    </svg>
                    <div class="rb-progress-percent">{ats_score}%</div>
                  </div>
                  <div class="rb-progress-info">
                    <div class="rb-progress-label">ATS Readiness</div>
                    <div class="rb-progress-status {ats_cls}">{ats_lbl}</div>
                  </div>
                </div>
                """
            ),
            unsafe_allow_html=True
        )

def kpi_card_html(label: str, value: str, hint: str, color: str) -> str:
    """Returns the HTML string for an enhanced KPI card (for backward compatibility)."""
    return (
        f'<div class="kpi-enhanced {color}">'
        f'<div class="kpi-lbl2">{label}</div>'
        f'<div class="kpi-val2 {color}">{value}</div>'
        f'<div class="kpi-hint2">{hint}</div>'
        f'</div>'
    )

def render_kpi_card(label: str, value: str, hint: str, color: str):
    """Renders an enhanced KPI card directly in Streamlit (for backward compatibility)."""
    st.markdown(kpi_card_html(label, value, hint, color), unsafe_allow_html=True)


