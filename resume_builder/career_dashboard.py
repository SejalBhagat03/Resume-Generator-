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

def show_career_center():
    st.markdown("## 💼 Career Center & Insights")
    st.markdown("Optimize, analyze, and manage multiple resume versions synchronized with a Master Profile.")
    
    d = st.session_state.resume
    ensure_setup(d)
    
    # -------------------------------------------------------------------------
    # 1. VERSION CONTROLLER & MASTER PROFILE INITIALIZER
    # -------------------------------------------------------------------------
    versions = list_versions()
    
    v_col1, v_col2 = st.columns([2, 1])
    with v_col1:
        # Version selection dropdown
        options = ["Default Workspace"] + versions
        current_version = st.session_state.get("active_version", "Default Workspace")
        if current_version not in options:
            current_version = "Default Workspace"
            
        selected_option = st.selectbox(
            "Active Resume Version",
            options=options,
            index=options.index(current_version)
        )
        
        if selected_option != current_version:
            st.session_state.active_version = selected_option
            if selected_option == "Default Workspace":
                # Fall back to root resume.json
                from resume_builder.app import load_from_disk
                st.session_state.resume = load_from_disk()
            else:
                # Load selected version with master profile inheritance
                st.session_state.resume = load_version(selected_option)
            st.session_state.last_hash = ""  # force PDF rebuild
            st.success(f"Loaded version: {selected_option}")
            st.rerun()
            
    with v_col2:
        # Save current state as new version
        new_version_name = st.text_input("Save active workspace as a new version", placeholder="e.g. frontend_developer")
        if st.button("💾 Save As Version", use_container_width=True):
            if new_version_name:
                clean_name = new_version_name.strip().lower().replace(" ", "_")
                save_version(clean_name, d)
                st.session_state.active_version = clean_name
                st.success(f"Successfully saved and switched to version: {clean_name}")
                st.rerun()
            else:
                st.error("Please enter a version name.")

    # -------------------------------------------------------------------------
    # 2. RUN CALCULATORS & METRICS ROW
    # -------------------------------------------------------------------------
    cc_res = ConsistencyChecker.analyze(d)
    
    # Selected target role for gap analysis
    target_role = st.session_state.get("target_role", "Frontend Developer")
    gap_res = CareerGapAnalyzer.analyze(d, target_role)
    
    # Skill evidence calculations
    gh_username = st.session_state.get("github_username", "")
    evidence = EvidenceSystem.calculate_evidence(d, gh_username)
    evidence_score = int(sum(e["confidence"] for e in evidence) / len(evidence)) if evidence else 0
    
    # Dashboard KPIs row
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    with kpi_col1:
        st.metric(label="Consistency Score", value=f"{cc_res['score']}%")
    with kpi_col2:
        st.metric(label="Evidence Score", value=f"{evidence_score}%")
    with kpi_col3:
        st.metric(label="Career Match Score", value=f"{gap_res['match_pct']}%")
    with kpi_col4:
        st.metric(label="Warnings Count", value=len(cc_res["warnings"]))

    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
    
    # -------------------------------------------------------------------------
    # 3. TABBED EXPANDERS (THE CAREER TOOLS)
    # -------------------------------------------------------------------------
    tabs = st.tabs([
        "👤 Master Profile Sync",
        "🔍 Consistency Checker",
        "🎯 Career Gap Analyzer",
        "💡 Achievement Quantifier",
        "🤝 Interview Prep Mode",
        "🐙 GitHub Evidence",
        "📝 Project Story Gen",
        "🕸️ Knowledge Graph"
    ])
    
    # --- TAB 1: MASTER PROFILE ---
    with tabs[0]:
        st.subheader("👤 Master Profile inheritance")
        st.markdown(
            "Below fields are marked as **Common Master Fields**. Any modification made here will automatically propagate "
            "to **all** saved resume versions (like frontend, backend, fullstack)."
        )
        
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
        m_email = st.text_input("Master Email", value=m_personal.get("email", ""), key="m_em")
        m_phone = st.text_input("Master Phone", value=m_personal.get("phone", ""), key="m_ph")
        m_loc = st.text_input("Master Location", value=m_personal.get("location", ""), key="m_lc")
        
        m_sk = master.get("technical_skills", {})
        st.markdown("#### Master Core Skills")
        edited_sk = {}
        for idx, (cat, val) in enumerate(m_sk.items()):
            edited_val = st.text_input(f"{cat}", value=val, key=f"m_sk_{idx}")
            edited_sk[cat] = edited_val
            
        if st.button("🔄 Sync Master Profile & Update All Resumes", type="primary"):
            master["personal"]["email"] = m_email
            master["personal"]["phone"] = m_phone
            master["personal"]["location"] = m_loc
            master["technical_skills"] = edited_sk
            
            # Write master and update active state
            save_master_profile(master)
            d.update(master)
            
            # Save the active memory state, sync master, and write backups
            save_active_resume_and_sync(d, None if selected_option == "Default Workspace" else selected_option)
            st.session_state.resume = d
            st.session_state.last_hash = "" # force recompile
            st.success("✅ Master Profile updated! All resume versions are synchronized.")
            st.rerun()

    # --- TAB 2: CONSISTENCY CHECKER ---
    with tabs[1]:
        st.subheader("🔍 Resume Consistency Check")
        st.markdown("Locate contradictions, empty fields, and unsupported statements.")
        
        if not cc_res["warnings"]:
            st.success("🎉 Excellent! No consistency issues detected in your resume data.")
        else:
            for w in cc_res["warnings"]:
                sev_color = "red" if w["severity"] == "high" else ("orange" if w["severity"] == "medium" else "blue")
                st.markdown(
                    f'<div style="background-color:#FAFAFC; border-left: 4px solid {sev_color}; padding:10px 12px; margin-bottom:10px; border-radius:4px; color:#1E293B;">'
                    f'<strong style="color:#1E293B;">{w["message"]}</strong><br/>'
                    f'<span style="color:#64748B; font-size:.8rem;">💡 Suggestion: {w["suggestion"]}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

    # --- TAB 3: CAREER GAP ANALYZER ---
    with tabs[2]:
        st.subheader("🎯 Target Role Gap Analysis")
        st.markdown("Check matching capability ratios and outline learning tracks.")
        
        roles_list = list(CareerGapAnalyzer.ROLE_REQUIREMENTS.keys())
        sel_role = st.selectbox("Select Target Career Role", options=roles_list, index=roles_list.index(target_role))
        
        if sel_role != target_role:
            st.session_state.target_role = sel_role
            st.rerun()
            
        st.markdown(f"### Matching Rating: **{gap_res['match_pct']}%**")
        st.progress(gap_res["match_pct"] / 100.0)
        
        # Grid display matching vs missing
        m1, m2 = st.columns(2)
        with m1:
            st.markdown("##### ✓ Matching Skills")
            if gap_res["matching"]:
                st.write(", ".join(gap_res["matching"]))
            else:
                st.info("No matching skills found. Time to add some!")
        with m2:
            st.markdown("##### ❌ Missing Skills")
            if gap_res["missing"]:
                st.write(", ".join(gap_res["missing"]))
            else:
                st.success("You possess all required skills for this role!")

        st.markdown("#### 🛠️ Recommended Learning Path")
        for rec in gap_res["learning_path"]:
            st.markdown(f"**{rec['priority']}. {rec['skill']}**\n> {rec['action']}")

    # --- TAB 4: ACHIEVEMENT QUANTIFIER ---
    with tabs[3]:
        st.subheader("💡 Bullet Points Quantifier")
        st.markdown("Improve plain statements by translating achievements into impactful, metric-based summaries.")
        
        quant_suggestions = AchievementQuantifier.analyze_bullets(d)
        if not quant_suggestions:
            st.success("🎉 High quality! All your bullet points have successfully integrated quantitative metrics.")
        else:
            for idx, sugg in enumerate(quant_suggestions):
                st.markdown(f"**Location: {sugg['section']} → {sugg['item_title']}**")
                st.info(f"**Original**: \"{sugg['original']}\"")
                st.success(f"**Suggested**: \"{sugg['improved']}\"")
                st.caption(f"**Reasoning**: {sugg['reason']}")
                
                # Button to apply directly
                if st.button("Apply Suggestion", key=f"apply_quant_{idx}"):
                    sec_name = sugg["section"].lower()
                    item_idx = sugg["item_index"]
                    bullet_idx = sugg["bullet_index"]
                    
                    # Update local state
                    st.session_state.resume[sec_name][item_idx]["bullets"][bullet_idx] = sugg["improved"]
                    # Save and sync
                    save_active_resume_and_sync(st.session_state.resume, None if selected_option == "Default Workspace" else selected_option)
                    st.session_state.last_hash = "" # force recompile
                    st.session_state.navigation_page = "workspace"
                    st.session_state.editor_notification = f"📈 Successfully applied metric-focused suggestion: \"{sugg['improved']}\"! Check the **{sugg['section']}** tab below."
                    st.rerun()
                st.markdown("---")

    # --- TAB 5: INTERVIEW PREP MODE ---
    with tabs[4]:
        st.subheader("🤝 Interview Prep Material Generator")
        st.markdown("Generate probable behavioral, project, and technical questions based on your resume details.")
        
        prep_data = InterviewPrep.generate_questions(d)
        
        st.markdown("#### 👤 Behavioral (HR) Questions")
        for q in prep_data["hr"]:
            with st.expander(f"Question: {q['question']}"):
                st.markdown(f"**Interviewer Intent**: *{q['reason']}*")
                st.markdown("**Expected Topics to Cover**:")
                for topic in q["expected_topics"]:
                    st.markdown(f"- {topic}")
                    
        st.markdown("#### 🚀 Project Architecture Questions")
        for q in prep_data["projects"]:
            with st.expander(f"[{q['project']}] {q['question']}"):
                st.markdown(f"**Interviewer Intent**: *{q['reason']}*")
                st.markdown("**Expected Topics to Cover**:")
                for topic in q["expected_topics"]:
                    st.markdown(f"- {topic}")

        st.markdown("#### 🛠️ Tech Stack Questions")
        for q in prep_data["technical"]:
            with st.expander(f"[{q['skill']}] {q['question']}"):
                st.markdown(f"**Interviewer Intent**: *{q['reason']}*")
                st.markdown("**Expected Topics to Cover**:")
                for topic in q["expected_topics"]:
                    st.markdown(f"- {topic}")

    # --- TAB 6: GITHUB EVIDENCE SYSTEM ---
    with tabs[5]:
        st.subheader("🐙 GitHub Repository Importer")
        st.markdown("Enter your GitHub username to browse your public repos and **add any project directly to your resume** in one click.")

        # ── Persist username in a small config file so it survives restarts ──
        import json as _json
        _cfg_path = os.path.join(os.path.dirname(__file__), "data", "github_config.json")
        os.makedirs(os.path.dirname(_cfg_path), exist_ok=True)

        # Load saved username if session_state is empty
        if not st.session_state.get("github_username"):
            try:
                with open(_cfg_path, "r") as _f:
                    st.session_state.github_username = _json.load(_f).get("username", "")
            except Exception:
                pass

        gh_username = st.session_state.get("github_username", "")

        # ── Username input row ──
        col_user, col_load = st.columns([3, 1])
        with col_user:
            username_input = st.text_input(
                "GitHub Username",
                value=gh_username,
                placeholder="e.g. SejalBhagat03",
                key="gh_username_input",
                label_visibility="collapsed",
            )
        with col_load:
            load_clicked = st.button("🔍 Load Repos", use_container_width=True, type="primary")

        # Save username on change
        if username_input != gh_username:
            st.session_state.github_username = username_input
            try:
                with open(_cfg_path, "w") as _f:
                    _json.dump({"username": username_input}, _f)
            except Exception:
                pass

        # ── Trigger load ──
        if load_clicked:
            st.session_state["gh_load_triggered"] = True

        if not username_input:
            st.info("👆 Enter your GitHub username above and click **🔍 Load Repos** to see your repositories.")
        elif not st.session_state.get("gh_load_triggered"):
            st.info(f"Click **🔍 Load Repos** to fetch repositories for **{username_input}**.")
        else:
            with st.spinner(f"Fetching repos for {username_input}…"):
                gh_analysis = GitHubIntegration.analyze_profile(username_input)

            score = gh_analysis.get("evidence_score", 0)
            score_color = "#10B981" if score >= 70 else ("#F59E0B" if score >= 40 else "#EF4444")
            st.markdown(
                f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;'
                f'padding:12px 16px;margin-bottom:12px;display:flex;align-items:center;gap:12px;">'
                f'<span style="font-size:1.6rem;font-weight:800;color:{score_color};">{score}/100</span>'
                f'<span style="color:#475569;font-size:.88rem;">GitHub Evidence Score — higher means more of your resume skills are proven by actual repos.</span>'
                f'</div>',
                unsafe_allow_html=True
            )

            projs = gh_analysis.get("suggested_projects", [])

            # ── Skill Confidence Metrics (the section that was here before) ──
            st.markdown("#### 🛠️ Skill Match — Resume vs GitHub")
            evidence = EvidenceSystem.calculate_evidence(d, username_input)
            if evidence:
                for e in evidence:
                    if e["confidence"] >= 80:
                        badge = "🟢"
                        badge_label = "Strong Evidence"
                        bar_color = "#10B981"
                    elif e["confidence"] >= 40:
                        badge = "🟡"
                        badge_label = "Moderate Evidence"
                        bar_color = "#F59E0B"
                    else:
                        badge = "🔴"
                        badge_label = "Unsupported"
                        bar_color = "#EF4444"

                    sources_text = ", ".join(e["sources"]) if e["sources"] else "Not found in GitHub repos"
                    pct = e["confidence"]
                    st.markdown(
                        f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;'
                        f'padding:10px 14px;margin-bottom:6px;">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">'
                        f'<span style="font-weight:700;color:#1E293B;font-size:.88rem;">{badge} {e["skill"]}</span>'
                        f'<span style="font-size:.78rem;color:#64748B;font-weight:600;">{pct}% · {badge_label}</span>'
                        f'</div>'
                        f'<div style="background:#E2E8F0;border-radius:100px;height:6px;">'
                        f'<div style="background:{bar_color};width:{pct}%;height:6px;border-radius:100px;"></div>'
                        f'</div>'
                        f'<div style="margin-top:4px;font-size:.75rem;color:#94A3B8;">📂 {sources_text}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.info("Add some technical skills to your resume to see skill match results here.")

            st.markdown("---")

            if not projs:
                st.warning(f"No public repositories found for **{username_input}**. Make sure the username is correct and repos are public.")
            else:
                st.markdown(f"### 📦 {len(projs)} Repositories Found — Click any to add to your resume:")
                for proj in projs:
                    # Check if this repo is already in the resume
                    existing_titles = [p.get("title", "").lower() for p in st.session_state.resume.get("projects", [])]
                    already_added = proj["name"].lower() in existing_titles

                    with st.expander(f"📁 **{proj['name']}**  ·  {proj['tech'] or 'General'}" + (" ✅" if already_added else ""), expanded=False):
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
                                if st.button(
                                    "➕ Add to Resume",
                                    key=f"add_git_proj_{proj['name']}",
                                    use_container_width=True,
                                    type="primary",
                                ):
                                    new_proj = {
                                        "title": proj["name"],
                                        "link": proj["url"],
                                        "date": "Present",
                                        "tools": proj["tech"] or "",
                                        "bullets": [proj["suggested_bullet"]],
                                    }
                                    active_res = st.session_state.resume
                                    if "projects" not in active_res:
                                        active_res["projects"] = []
                                    active_res["projects"].append(new_proj)
                                    st.session_state.resume = active_res
                                    save_active_resume_and_sync(
                                        active_res,
                                        None if selected_option == "Default Workspace" else selected_option,
                                    )
                                    st.session_state.last_hash = ""
                                    st.session_state.navigation_page = "workspace"
                                    st.session_state.editor_notification = (
                                        f"🎉 Added **{proj['name']}** from GitHub to your resume! "
                                        f"Click the **🚀 Projects** tab below to view and edit it."
                                    )
                                    st.rerun()

    # --- TAB 7: PROJECT STORY GENERATOR ---
    with tabs[6]:
        st.subheader("📝 Project Narrative & Bio Builder")
        st.markdown("Translate basic tech setups into standard bullet lists, LinkedIn summaries, and interview talking points.")
        
        story_name = st.text_input("Project Name", placeholder="e.g. Labour Management App", key="story_name")
        story_tech = st.text_input("Tech Stack", placeholder="e.g. React, Node.js, MongoDB", key="story_tech")
        story_desc = st.text_area("Short description of what it does", placeholder="e.g. A database tool that displays labor logs and material tracking on dynamic layouts.", key="story_desc")
        
        if st.button("Generate Story Copy"):
            if story_name and story_tech and story_desc:
                res = ProjectStoryGenerator.generate_story(story_name, story_tech, story_desc)
                
                st.markdown("#### 📄 Suggested Resume Bullets")
                for b in res["bullets"]:
                    st.info(b)
                    
                st.markdown("#### 🔗 LinkedIn Announcement Summary")
                st.code(res["linkedin"], language="text")
                
                st.markdown("#### 🌐 Web Portfolio Section")
                st.markdown(res["portfolio"])
                
                st.markdown("#### 🤝 Interview Explanation (STAR Framework)")
                st.markdown(f"**S (Situation)**: {res['star']['situation']}")
                st.markdown(f"**T (Task)**: {res['star']['task']}")
                st.markdown(f"**A (Action)**: {res['star']['action']}")
                st.markdown(f"**R (Result)**: {res['star']['result']}")
            else:
                st.error("Please fill in all details to generate project story.")

    # --- TAB 8: RESUME KNOWLEDGE GRAPH ---
    with tabs[7]:
        st.subheader("🕸️ Resume Connections Knowledge Graph")
        st.markdown("Visual mapping linking your Skills to the Projects and Experience entries demonstrating them.")
        
        graph_html = KnowledgeGraphRenderer.render_graph_html(d)
        import streamlit.components.v1 as components
        components.html(graph_html, height=500, scrolling=True)

