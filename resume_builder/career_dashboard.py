import streamlit as st
import json
import os
import copy
from resume_builder.utils.master_profile import (
    ensure_setup, load_master_profile, save_master_profile,
    list_versions, load_version, save_version, update_resume_with_master, save_active_resume_and_sync
)
from resume_builder.utils.consistency_checker import ConsistencyChecker
from resume_builder.utils.achievement_quantifier import AchievementQuantifier
from resume_builder.utils.gap_analyzer import CareerGapAnalyzer
from resume_builder.utils.interview_prep import InterviewPrep
from resume_builder.utils.github_integration import GitHubIntegration
from resume_builder.utils.evidence_system import EvidenceSystem
from resume_builder.utils.project_story import ProjectStoryGenerator
from resume_builder.utils.knowledge_graph import KnowledgeGraphRenderer

# ─── Tool Definitions ────────────────────────────────────────────────────────
CAREER_TOOLS = [
    {
        "id":    "master_sync",
        "icon":  "👤",
        "title": "Master Profile Sync",
        "desc":  "One edit updates ALL resume versions at once",
        "how":   "Edit your shared contact info and core skills below, then click <b>Sync</b> — every saved version updates automatically.",
    },
    {
        "id":    "consistency",
        "icon":  "🔍",
        "title": "Consistency Checker",
        "desc":  "Catch contradictions and empty fields",
        "how":   "Each warning below points to a real issue. Fix <b>high-severity (🔴)</b> ones first — they hurt ATS rankings most.",
    },
    {
        "id":    "gap_analyzer",
        "icon":  "🎯",
        "title": "Career Gap Analyzer",
        "desc":  "See skill gaps vs your target role",
        "how":   "Select a target job role, then check your match percentage and follow the recommended learning path below.",
    },
    {
        "id":    "achievements",
        "icon":  "💡",
        "title": "Achievement Quantifier",
        "desc":  "Turn vague bullets into impact statements",
        "how":   "Review each suggested rewrite and click <b>Apply</b> to instantly swap it into your resume.",
    },
    {
        "id":    "interview_prep",
        "icon":  "🤝",
        "title": "Interview Prep Mode",
        "desc":  "Get likely interview questions per role",
        "how":   "Expand any question to see what the interviewer is testing and which topics you should cover in your answer.",
    },
    {
        "id":    "github",
        "icon":  "🐙",
        "title": "GitHub Evidence",
        "desc":  "Prove your skills with real repos",
        "how":   "Enter your GitHub username and click <b>Load Repos</b>. Then add any project to your resume in one click.",
    },
    {
        "id":    "project_story",
        "icon":  "📝",
        "title": "Project Story Gen",
        "desc":  "Generate bullets, LinkedIn posts & STAR answers",
        "how":   "Fill in the project name, tech stack, and a brief description. Then click <b>Generate</b> to get resume bullets, a LinkedIn post, and a STAR interview answer.",
    },
    {
        "id":    "knowledge_graph",
        "icon":  "🕸️",
        "title": "Knowledge Graph",
        "desc":  "See how your skills & experience connect",
        "how":   "The graph links every skill to the project or job where you used it. Hover over nodes to see details.",
    },
]

# ─── Career Center CSS ───────────────────────────────────────────────────────
_CAREER_CSS = """
<style>
/* ── Hero ──────────────────────────────────────────────────────────────── */
.career-hero {
    background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
    border-radius: 16px;
    padding: 26px 32px;
    margin-bottom: 20px;
}
.career-hero h1 {
    color: #fff !important;
    font-size: 1.55rem;
    font-weight: 800;
    margin: 0 0 6px;
    letter-spacing: -.02em;
}
.career-hero p {
    color: rgba(255,255,255,.88) !important;
    font-size: .9rem;
    margin: 0;
    line-height: 1.5;
}

/* ── KPI Cards ──────────────────────────────────────────────────────────── */
.kpi-enhanced {
    background: #fff;
    border-radius: 12px;
    border: 1.5px solid #E2E8F0;
    padding: 14px 16px 12px;
    position: relative;
    overflow: hidden;
    height: 100%;
}
.kpi-enhanced::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 4px;
    border-radius: 12px 0 0 12px;
}
.kpi-enhanced.kpi-green::before { background: #10B981; }
.kpi-enhanced.kpi-amber::before  { background: #F59E0B; }
.kpi-enhanced.kpi-red::before    { background: #EF4444; }
.kpi-enhanced.kpi-blue::before   { background: #3B82F6; }

.kpi-lbl2 {
    font-size: .63rem;
    font-weight: 700;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: .08em;
    margin-bottom: 5px;
}
.kpi-val2 {
    font-size: 1.85rem;
    font-weight: 800;
    line-height: 1.1;
    color: #1E293B;
}
.kpi-val2.kpi-green { color: #10B981 !important; }
.kpi-val2.kpi-amber  { color: #F59E0B !important; }
.kpi-val2.kpi-red    { color: #EF4444 !important; }
.kpi-val2.kpi-blue   { color: #3B82F6 !important; }
.kpi-hint2 {
    font-size: .72rem;
    color: #64748B;
    margin-top: 5px;
    line-height: 1.35;
}

/* ── Tool Card Buttons (via Streamlit button) ──────────────────────────── */
/* We layer a caption under each button — see Python code */

/* ── Section Title ─────────────────────────────────────────────────────── */
.cc-section-title {
    font-size: .76rem;
    font-weight: 700;
    color: #6366F1;
    text-transform: uppercase;
    letter-spacing: .09em;
    margin: 22px 0 10px;
    padding-bottom: 5px;
    border-bottom: 2px solid #EEF2FF;
}

/* ── Active Tool Header ─────────────────────────────────────────────────── */
.cc-tool-header {
    display: flex;
    align-items: center;
    gap: 12px;
    background: #F8FAFC;
    border: 1.5px solid #E2E8F0;
    border-radius: 12px;
    padding: 14px 18px;
    margin: 8px 0 16px;
}
.cc-tool-icon { font-size: 1.6rem; }
.cc-tool-title {
    font-size: 1.1rem;
    font-weight: 800;
    color: #1E293B;
    margin: 0 0 2px;
    letter-spacing: -.01em;
}
.cc-tool-desc  { font-size: .82rem; color: #64748B; margin: 0; }

/* ── How-to-use Callout ─────────────────────────────────────────────────── */
.cc-how-to {
    background: #F0FDF4;
    border: 1px solid #BBF7D0;
    border-left: 4px solid #10B981;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 18px;
    font-size: .83rem;
    color: #166534;
    line-height: 1.5;
}
.cc-how-to b { color: #15803D; }

/* ── Skill Pill Tags ────────────────────────────────────────────────────── */
.skill-pill-green {
    display: inline-block;
    background: #DCFCE7;
    color: #15803D;
    padding: 3px 10px;
    border-radius: 100px;
    font-size: .76rem;
    font-weight: 600;
    margin: 2px 3px 2px 0;
}
.skill-pill-red {
    display: inline-block;
    background: #FEE2E2;
    color: #B91C1C;
    padding: 3px 10px;
    border-radius: 100px;
    font-size: .76rem;
    font-weight: 600;
    margin: 2px 3px 2px 0;
}

/* ── Achievement Cards ──────────────────────────────────────────────────── */
.ach-card {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 12px;
}
.ach-section-tag {
    font-size: .65rem;
    font-weight: 700;
    color: #6366F1;
    text-transform: uppercase;
    letter-spacing: .07em;
    margin-bottom: 8px;
}
.ach-original {
    background: #FEF2F2;
    border-radius: 6px;
    padding: 8px 12px;
    margin-bottom: 8px;
    font-size: .83rem;
    color: #7f1d1d;
}
.ach-improved {
    background: #F0FDF4;
    border-radius: 6px;
    padding: 8px 12px;
    margin-bottom: 8px;
    font-size: .83rem;
    color: #14532d;
}
.ach-reason {
    font-size: .76rem;
    color: #64748B;
}
</style>
"""


# ─── Helper Functions ─────────────────────────────────────────────────────────
def _score_color(score: int, invert: bool = False) -> str:
    """Return CSS class ('kpi-green' / 'kpi-amber' / 'kpi-red') for a score."""
    if invert:
        return "kpi-green" if score == 0 else ("kpi-amber" if score < 10 else "kpi-red")
    return "kpi-green" if score >= 70 else ("kpi-amber" if score >= 40 else "kpi-red")


def _kpi_card(label: str, value: str, hint: str, color: str) -> str:
    return (
        f'<div class="kpi-enhanced {color}">'
        f'<div class="kpi-lbl2">{label}</div>'
        f'<div class="kpi-val2 {color}">{value}</div>'
        f'<div class="kpi-hint2">{hint}</div>'
        f'</div>'
    )


def _how_to(text: str):
    st.markdown(f'<div class="cc-how-to">💡 <b>How to use:</b> {text}</div>', unsafe_allow_html=True)


def _section_title(text: str):
    st.markdown(f'<div class="cc-section-title">{text}</div>', unsafe_allow_html=True)


# ─── Main Entry Point ─────────────────────────────────────────────────────────
def show_career_center():
    st.markdown(_CAREER_CSS, unsafe_allow_html=True)

    d = st.session_state.resume
    ensure_setup(d)

    # ── Initialize active tool ─────────────────────────────────────────────
    if "career_active_tool" not in st.session_state:
        st.session_state.career_active_tool = "master_sync"

    # ── Compute all metrics up-front ───────────────────────────────────────
    cc_res      = ConsistencyChecker.analyze(d)
    target_role = st.session_state.get("target_role", "Frontend Developer")
    gap_res     = CareerGapAnalyzer.analyze(d, target_role)
    gh_username = st.session_state.get("github_username", "")
    evidence    = EvidenceSystem.calculate_evidence(d, gh_username)
    ev_score    = int(sum(e["confidence"] for e in evidence) / len(evidence)) if evidence else 0

    # ── Resolve current version ────────────────────────────────────────────
    versions = list_versions()
    selected_option = st.session_state.get("active_version", "Default Workspace")
    if selected_option not in (["Default Workspace"] + versions):
        selected_option = "Default Workspace"

    # ══════════════════════════════════════════════════════════════════════
    # HERO SECTION
    # ══════════════════════════════════════════════════════════════════════
    st.markdown(
        '<div class="career-hero">'
        '<h1>💼 Career Center</h1>'
        '<p>Your 8-tool career lab. Analyze gaps, prove skills, and manage multiple tailored resume versions — all in one place.<br>'
        '<span style="opacity:.75;font-size:.82rem;">Pick a tool from the grid below to get started.</span></p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════════════════════════════════
    # VERSION MANAGER  (collapsible — doesn't dominate the page)
    # ══════════════════════════════════════════════════════════════════════
    with st.expander(
        f"📁 Resume Versions  ·  {'**' + selected_option + '**' if selected_option != 'Default Workspace' else 'Default Workspace'}  —  click to save or switch",
        expanded=False,
    ):
        _how_to(
            "Save your current workspace as a named version (e.g. <b>frontend_developer</b>), "
            "then switch between versions using the dropdown. All versions inherit Master Profile data."
        )
        v_col1, v_col2 = st.columns([2, 1])
        with v_col1:
            options = ["Default Workspace"] + versions
            sel = st.selectbox(
                "Active Resume Version",
                options=options,
                index=options.index(selected_option),
                key="career_version_select",
            )
            if sel != selected_option:
                st.session_state.active_version = sel
                if sel == "Default Workspace":
                    from resume_builder.app import load_from_disk
                    st.session_state.resume = load_from_disk()
                else:
                    st.session_state.resume = load_version(sel)
                st.session_state.last_hash = ""
                selected_option = sel
                st.success(f"✅ Loaded version: **{sel}**")
                st.rerun()

        with v_col2:
            new_ver = st.text_input(
                "Save as new version",
                placeholder="e.g. frontend_developer",
                key="career_new_ver",
            )
            if st.button("💾 Save As Version", use_container_width=True, type="primary"):
                if new_ver:
                    clean = new_ver.strip().lower().replace(" ", "_")
                    save_version(clean, d)
                    st.session_state.active_version = clean
                    selected_option = clean
                    st.success(f"✅ Saved: **{clean}**")
                    st.rerun()
                else:
                    st.error("Please enter a version name.")

        if versions:
            st.markdown(
                f"**{len(versions)} saved version(s):** "
                + "  ".join(f"`{v}`" for v in versions)
            )
        else:
            st.caption("No saved versions yet. Use the field above to save your first one.")

    # ══════════════════════════════════════════════════════════════════════
    # KPI ROW — color-coded with explanations
    # ══════════════════════════════════════════════════════════════════════
    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    con_cls  = _score_color(cc_res["score"])
    ev_cls   = _score_color(ev_score)
    gap_cls  = _score_color(gap_res["match_pct"])
    warn_cls = _score_color(len(cc_res["warnings"]), invert=True)

    with k1:
        st.markdown(
            _kpi_card("Consistency Score", f"{cc_res['score']}%",
                      "Data accuracy across all sections", con_cls),
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            _kpi_card("Evidence Score", f"{ev_score}%",
                      "Resume skills proven by GitHub", ev_cls),
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            _kpi_card("Career Match", f"{gap_res['match_pct']}%",
                      f"Match vs {target_role}", gap_cls),
            unsafe_allow_html=True,
        )
    with k4:
        w_count = len(cc_res["warnings"])
        st.markdown(
            _kpi_card("Warnings", str(w_count),
                      "Issues to fix (0 is ideal)", warn_cls),
            unsafe_allow_html=True,
        )

    # ══════════════════════════════════════════════════════════════════════
    # FEATURE CARD GRID — tool navigation
    # ══════════════════════════════════════════════════════════════════════
    _section_title("🛠️ Career Tools — click any card to open")

    # Row 1: first 4 tools
    row1 = st.columns(4)
    for i, tool in enumerate(CAREER_TOOLS[:4]):
        with row1[i]:
            is_active = st.session_state.career_active_tool == tool["id"]
            clicked = st.button(
                f"{tool['icon']} **{tool['title']}**",
                key=f"tool_btn_{tool['id']}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            )
            st.caption(tool["desc"])
            if clicked:
                st.session_state.career_active_tool = tool["id"]
                st.rerun()

    # Row 2: next 4 tools
    row2 = st.columns(4)
    for i, tool in enumerate(CAREER_TOOLS[4:]):
        with row2[i]:
            is_active = st.session_state.career_active_tool == tool["id"]
            clicked = st.button(
                f"{tool['icon']} **{tool['title']}**",
                key=f"tool_btn_{tool['id']}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            )
            st.caption(tool["desc"])
            if clicked:
                st.session_state.career_active_tool = tool["id"]
                st.rerun()

    # ══════════════════════════════════════════════════════════════════════
    # ACTIVE TOOL CONTENT AREA
    # ══════════════════════════════════════════════════════════════════════
    active_id   = st.session_state.career_active_tool
    active_tool = next((t for t in CAREER_TOOLS if t["id"] == active_id), CAREER_TOOLS[0])

    st.markdown(
        f'<div class="cc-tool-header">'
        f'<span class="cc-tool-icon">{active_tool["icon"]}</span>'
        f'<div><div class="cc-tool-title">{active_tool["title"]}</div>'
        f'<div class="cc-tool-desc">{active_tool["desc"]}</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    _how_to(active_tool["how"])

    # ── 1. MASTER PROFILE SYNC ────────────────────────────────────────────
    if active_id == "master_sync":
        master = load_master_profile()
        if not master:
            master = {
                "personal": d.get("personal", {}),
                "education": d.get("education", []),
                "technical_skills": d.get("technical_skills", {}),
                "achievements": d.get("achievements", []),
                "position_of_responsibility": d.get("position_of_responsibility", [])
            }
            save_master_profile(master)

        m_personal = master.get("personal", {})
        _section_title("Shared Contact Fields")
        mp1, mp2, mp3 = st.columns(3)
        with mp1:
            m_email = st.text_input("📧 Email", value=m_personal.get("email", ""), key="m_em")
        with mp2:
            m_phone = st.text_input("📞 Phone", value=m_personal.get("phone", ""), key="m_ph")
        with mp3:
            m_loc   = st.text_input("📍 Location", value=m_personal.get("location", ""), key="m_lc")

        m_sk = master.get("technical_skills", {})
        _section_title("Master Core Skills")
        edited_sk = {}
        for idx, (cat, val) in enumerate(m_sk.items()):
            sc1, sc2 = st.columns([.35, .65])
            with sc1:
                st.text_input("Category", cat, key=f"m_sk_lbl_{idx}",
                              label_visibility="collapsed", disabled=True)
            with sc2:
                edited_val = st.text_input("Skills", val, key=f"m_sk_{idx}",
                                           label_visibility="collapsed")
            edited_sk[cat] = edited_val

        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
        if st.button("🔄 Sync Master Profile & Update All Resumes", type="primary", use_container_width=True):
            master["personal"]["email"]    = m_email
            master["personal"]["phone"]    = m_phone
            master["personal"]["location"] = m_loc
            master["technical_skills"]     = edited_sk
            save_master_profile(master)
            d.update(master)
            save_active_resume_and_sync(
                d, None if selected_option == "Default Workspace" else selected_option
            )
            st.session_state.resume    = d
            st.session_state.last_hash = ""
            st.success("✅ Master Profile updated! All resume versions are synchronized.")
            st.rerun()

    # ── 2. CONSISTENCY CHECKER ────────────────────────────────────────────
    elif active_id == "consistency":
        if not cc_res["warnings"]:
            st.success("🎉 Excellent! No consistency issues detected in your resume.")
        else:
            st.markdown(
                f'<div style="background:#FFF7ED;border:1px solid #FED7AA;border-radius:8px;'
                f'padding:10px 14px;margin-bottom:16px;font-size:.85rem;color:#92400E;">'
                f'⚠️ <b>{len(cc_res["warnings"])} issue(s) found.</b> '
                f'Fix 🔴 <b>HIGH</b> severity issues first — they have the biggest impact on ATS scores.'
                f'</div>',
                unsafe_allow_html=True,
            )
            for w in cc_res["warnings"]:
                sev        = w["severity"]
                sev_color  = "#EF4444" if sev == "high" else ("#F59E0B" if sev == "medium" else "#3B82F6")
                sev_label  = sev.upper()
                sev_icon   = "🔴" if sev == "high" else ("🟡" if sev == "medium" else "🔵")
                st.markdown(
                    f'<div style="background:#FAFAFC;border-left:4px solid {sev_color};'
                    f'padding:10px 14px;margin-bottom:10px;border-radius:6px;">'
                    f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">'
                    f'<span style="background:{sev_color};color:#fff;font-size:.64rem;font-weight:700;'
                    f'padding:2px 8px;border-radius:100px;">{sev_icon} {sev_label}</span>'
                    f'<strong style="color:#1E293B;font-size:.88rem;">{w["message"]}</strong></div>'
                    f'<span style="color:#64748B;font-size:.8rem;">💡 Suggestion: {w["suggestion"]}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # ── 3. CAREER GAP ANALYZER ────────────────────────────────────────────
    elif active_id == "gap_analyzer":
        roles_list = list(CareerGapAnalyzer.ROLE_REQUIREMENTS.keys())
        sel_role = st.selectbox(
            "🎯 Target Role",
            options=roles_list,
            index=roles_list.index(target_role),
            key="career_gap_role_sel",
        )
        if sel_role != target_role:
            st.session_state.target_role = sel_role
            st.rerun()

        match_pct  = gap_res["match_pct"]
        bar_color  = "#10B981" if match_pct >= 70 else ("#F59E0B" if match_pct >= 40 else "#EF4444")
        bar_label  = "Strong Match 🎉" if match_pct >= 70 else ("Getting There 💪" if match_pct >= 40 else "Needs Work 📚")

        st.markdown(
            f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:18px 20px;margin:12px 0;">'
            f'<div style="font-size:.65rem;font-weight:700;color:#94A3B8;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px;">Match Rating</div>'
            f'<div style="display:flex;align-items:flex-end;gap:12px;margin-bottom:10px;">'
            f'<span style="font-size:2.5rem;font-weight:800;color:{bar_color};">{match_pct}%</span>'
            f'<span style="font-size:.88rem;color:{bar_color};font-weight:600;margin-bottom:8px;">{bar_label}</span>'
            f'</div>'
            f'<div style="background:#E2E8F0;border-radius:100px;height:10px;">'
            f'<div style="background:{bar_color};width:{match_pct}%;height:10px;border-radius:100px;transition:width .4s;"></div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        m1, m2 = st.columns(2)
        with m1:
            _section_title("✅ Matching Skills")
            if gap_res["matching"]:
                pills = "".join(
                    f'<span class="skill-pill-green">{sk}</span>' for sk in gap_res["matching"]
                )
                st.markdown(pills, unsafe_allow_html=True)
            else:
                st.info("No matching skills found yet — add more to your resume!")
        with m2:
            _section_title("❌ Missing Skills")
            if gap_res["missing"]:
                pills = "".join(
                    f'<span class="skill-pill-red">{sk}</span>' for sk in gap_res["missing"]
                )
                st.markdown(pills, unsafe_allow_html=True)
            else:
                st.success("You have all required skills for this role!")

        if gap_res.get("learning_path"):
            _section_title("📚 Recommended Learning Path")
            for rec in gap_res["learning_path"]:
                st.markdown(
                    f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;'
                    f'padding:10px 14px;margin-bottom:8px;">'
                    f'<div style="font-weight:700;color:#1E293B;font-size:.88rem;margin-bottom:3px;">#{rec["priority"]} · {rec["skill"]}</div>'
                    f'<div style="color:#64748B;font-size:.82rem;">{rec["action"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # ── 4. ACHIEVEMENT QUANTIFIER ─────────────────────────────────────────
    elif active_id == "achievements":
        quant_suggestions = AchievementQuantifier.analyze_bullets(d)
        if not quant_suggestions:
            st.success("🎉 All bullet points already have strong quantitative metrics!")
        else:
            st.markdown(
                f'<div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:8px;'
                f'padding:10px 14px;margin-bottom:16px;font-size:.85rem;color:#1E40AF;">'
                f'📊 <b>{len(quant_suggestions)} bullet(s)</b> can be improved with metrics. '
                f'Click <b>Apply</b> to update your resume instantly.'
                f'</div>',
                unsafe_allow_html=True,
            )
            for idx, sugg in enumerate(quant_suggestions):
                st.markdown(
                    f'<div class="ach-card">'
                    f'<div class="ach-section-tag">📍 {sugg["section"]} → {sugg["item_title"]}</div>'
                    f'<div class="ach-original"><b>Original:</b> "{sugg["original"]}"</div>'
                    f'<div class="ach-improved"><b>Suggested:</b> "{sugg["improved"]}"</div>'
                    f'<div class="ach-reason">📖 Reasoning: {sugg["reason"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if st.button("✅ Apply Suggestion", key=f"apply_quant_{idx}", type="primary"):
                    sec_name   = sugg["section"].lower()
                    item_idx   = sugg["item_index"]
                    bullet_idx = sugg["bullet_index"]
                    st.session_state.resume[sec_name][item_idx]["bullets"][bullet_idx] = sugg["improved"]
                    save_active_resume_and_sync(
                        st.session_state.resume,
                        None if selected_option == "Default Workspace" else selected_option,
                    )
                    st.session_state.last_hash = ""
                    st.session_state.navigation_page = "workspace"
                    st.session_state.editor_notification = (
                        f"📈 Applied metric suggestion: \"{sugg['improved']}\"! "
                        f"Check the **{sugg['section']}** tab."
                    )
                    st.rerun()
                st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)

    # ── 5. INTERVIEW PREP MODE ────────────────────────────────────────────
    elif active_id == "interview_prep":
        prep_data = InterviewPrep.generate_questions(d)
        sections = [
            ("👤 Behavioral (HR) Questions",      prep_data.get("hr", []),        None),
            ("🚀 Project Architecture Questions",  prep_data.get("projects", []),  "project"),
            ("🛠️ Tech Stack Questions",             prep_data.get("technical", []), "skill"),
        ]
        for sec_title, questions, key_field in sections:
            _section_title(sec_title)
            if not questions:
                st.caption("No questions generated for this category yet.")
                continue
            for q in questions:
                label = q["question"]
                if key_field == "project":
                    label = f"[{q['project']}] {q['question']}"
                elif key_field == "skill":
                    label = f"[{q['skill']}] {q['question']}"
                with st.expander(label):
                    st.markdown(
                        f'<div style="background:#F8FAFC;border-left:3px solid #6366F1;'
                        f'padding:8px 12px;border-radius:4px;margin-bottom:8px;font-size:.84rem;">'
                        f'<i>Interviewer Intent:</i> <b>{q["reason"]}</b>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown("**Topics to cover in your answer:**")
                    for topic in q.get("expected_topics", []):
                        st.markdown(f"- {topic}")

    # ── 6. GITHUB EVIDENCE SYSTEM ─────────────────────────────────────────
    elif active_id == "github":
        import json as _json
        _cfg_path = os.path.join(os.path.dirname(__file__), "data", "github_config.json")
        os.makedirs(os.path.dirname(_cfg_path), exist_ok=True)

        if not st.session_state.get("github_username"):
            try:
                with open(_cfg_path, "r") as _f:
                    st.session_state.github_username = _json.load(_f).get("username", "")
            except Exception:
                pass

        gh_username = st.session_state.get("github_username", "")

        col_user, col_load = st.columns([3, 1])
        with col_user:
            username_input = st.text_input(
                "GitHub Username",
                value=gh_username,
                placeholder="e.g. SejalBhagat03",
                key="gh_username_input",
            )
        with col_load:
            st.markdown('<div style="height:28px"></div>', unsafe_allow_html=True)
            load_clicked = st.button("🔍 Load Repos", use_container_width=True, type="primary")

        if username_input != gh_username:
            st.session_state.github_username = username_input
            try:
                with open(_cfg_path, "w") as _f:
                    _json.dump({"username": username_input}, _f)
            except Exception:
                pass

        if load_clicked:
            st.session_state["gh_load_triggered"] = True

        if not username_input:
            st.info("👆 Enter your GitHub username above and click **🔍 Load Repos** to begin.")
        elif not st.session_state.get("gh_load_triggered"):
            st.info(f"Click **🔍 Load Repos** to fetch repositories for **{username_input}**.")
        else:
            with st.spinner(f"Fetching repos for {username_input}…"):
                gh_analysis = GitHubIntegration.analyze_profile(username_input)

            score       = gh_analysis.get("evidence_score", 0)
            score_color = "#10B981" if score >= 70 else ("#F59E0B" if score >= 40 else "#EF4444")
            st.markdown(
                f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;'
                f'padding:14px 18px;margin-bottom:16px;display:flex;align-items:center;gap:16px;">'
                f'<span style="font-size:2.2rem;font-weight:800;color:{score_color};">{score}/100</span>'
                f'<div><div style="font-weight:600;color:#1E293B;font-size:.88rem;">GitHub Evidence Score</div>'
                f'<div style="color:#64748B;font-size:.79rem;">Higher = more resume skills proven by actual repos</div></div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            _section_title("🛠️ Skill Match — Resume vs GitHub")
            ev_data = EvidenceSystem.calculate_evidence(d, username_input)
            if ev_data:
                for e in ev_data:
                    conf = e["confidence"]
                    badge     = "🟢" if conf >= 80 else ("🟡" if conf >= 40 else "🔴")
                    badge_lbl = "Strong Evidence" if conf >= 80 else ("Moderate" if conf >= 40 else "Unsupported")
                    bar_clr   = "#10B981" if conf >= 80 else ("#F59E0B" if conf >= 40 else "#EF4444")
                    sources   = ", ".join(e["sources"]) if e["sources"] else "Not found in GitHub repos"
                    st.markdown(
                        f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;'
                        f'padding:10px 14px;margin-bottom:6px;">'
                        f'<div style="display:flex;justify-content:space-between;margin-bottom:5px;">'
                        f'<span style="font-weight:700;color:#1E293B;">{badge} {e["skill"]}</span>'
                        f'<span style="font-size:.76rem;color:#64748B;font-weight:600;">{conf}% · {badge_lbl}</span>'
                        f'</div>'
                        f'<div style="background:#E2E8F0;border-radius:100px;height:6px;">'
                        f'<div style="background:{bar_clr};width:{conf}%;height:6px;border-radius:100px;"></div>'
                        f'</div>'
                        f'<div style="margin-top:4px;font-size:.74rem;color:#94A3B8;">📂 {sources}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.info("Add technical skills to your resume to see match results here.")

            projs = gh_analysis.get("suggested_projects", [])
            if projs:
                _section_title(f"📦 {len(projs)} Repositories Found — click to add")
                for proj in projs:
                    existing = [p.get("title", "").lower() for p in st.session_state.resume.get("projects", [])]
                    already_added = proj["name"].lower() in existing
                    with st.expander(
                        f"📁 **{proj['name']}**  ·  {proj['tech'] or 'General'}" + (" ✅" if already_added else ""),
                        expanded=False,
                    ):
                        col_desc, col_btn = st.columns([3, 1])
                        with col_desc:
                            st.markdown(f"**{proj['description']}**")
                            st.caption(f"🔗 [{proj['url']}]({proj['url']})")
                            st.code(proj["suggested_bullet"], language="text")
                        with col_btn:
                            st.markdown("<br>", unsafe_allow_html=True)
                            if already_added:
                                st.success("✅ Added")
                            else:
                                if st.button("➕ Add to Resume", key=f"add_git_proj_{proj['name']}",
                                             use_container_width=True, type="primary"):
                                    new_proj = {
                                        "title":   proj["name"],
                                        "link":    proj["url"],
                                        "date":    "Present",
                                        "tools":   proj["tech"] or "",
                                        "bullets": [proj["suggested_bullet"]],
                                    }
                                    active_res = st.session_state.resume
                                    active_res.setdefault("projects", []).append(new_proj)
                                    st.session_state.resume = active_res
                                    save_active_resume_and_sync(
                                        active_res,
                                        None if selected_option == "Default Workspace" else selected_option,
                                    )
                                    st.session_state.last_hash = ""
                                    st.session_state.navigation_page = "workspace"
                                    st.session_state.editor_notification = (
                                        f"🎉 Added **{proj['name']}** from GitHub! "
                                        f"Click the **🚀 Projects** tab to view it."
                                    )
                                    st.rerun()
            else:
                st.warning(
                    f"No public repositories found for **{username_input}**. "
                    "Make sure the username is correct and repos are public."
                )

    # ── 7. PROJECT STORY GENERATOR ────────────────────────────────────────
    elif active_id == "project_story":
        c1, c2 = st.columns(2)
        with c1:
            story_name = st.text_input(
                "Project Name", placeholder="e.g. Labour Management App", key="story_name"
            )
        with c2:
            story_tech = st.text_input(
                "Tech Stack", placeholder="e.g. React, Node.js, MongoDB", key="story_tech"
            )
        story_desc = st.text_area(
            "Short description of what it does",
            height=88,
            placeholder="e.g. A tool that tracks labor logs and material usage on dynamic dashboards.",
            key="story_desc",
        )

        if st.button("✨ Generate Story Copy", type="primary", use_container_width=True):
            if story_name and story_tech and story_desc:
                with st.spinner("Generating story content…"):
                    res = ProjectStoryGenerator.generate_story(story_name, story_tech, story_desc)

                out_t1, out_t2, out_t3, out_t4 = st.tabs([
                    "📄 Resume Bullets", "🔗 LinkedIn Post", "🌐 Portfolio Copy", "🤝 STAR Interview"
                ])
                with out_t1:
                    st.markdown("**Paste these directly into your resume bullets:**")
                    for b in res["bullets"]:
                        st.info(b)
                with out_t2:
                    st.markdown("**Copy-paste into LinkedIn:**")
                    st.code(res["linkedin"], language="text")
                with out_t3:
                    st.markdown(res["portfolio"])
                with out_t4:
                    star = res["star"]
                    for key, label in [
                        ("situation", "S — Situation"),
                        ("task",      "T — Task"),
                        ("action",    "A — Action"),
                        ("result",    "R — Result"),
                    ]:
                        st.markdown(
                            f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;'
                            f'padding:10px 14px;margin-bottom:8px;">'
                            f'<b style="color:#6366F1;">{label}</b><br/>'
                            f'<span style="color:#1E293B;font-size:.88rem;">{star[key]}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
            else:
                st.error("Please fill in all three fields to generate the story.")

    # ── 8. KNOWLEDGE GRAPH ────────────────────────────────────────────────
    elif active_id == "knowledge_graph":
        graph_html = KnowledgeGraphRenderer.render_graph_html(d)
        import streamlit.components.v1 as components
        components.html(graph_html, height=520, scrolling=True)
