import streamlit as st
import json
import os
import base64
from generate_resume import generate_pdf

# Set page configuration
st.set_page_config(
    page_title="Resume-as-Code Builder",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling using CSS injection
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

/* Apply font */
html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    font-family: 'Plus Jakarta Sans', 'Outfit', sans-serif;
}

/* Sleek title styling */
.gradient-title {
    background: linear-gradient(135deg, #1E40AF 0%, #3B82F6 50%, #8B5CF6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.8rem;
    font-weight: 800;
    text-align: center;
    margin-bottom: 0.2rem;
    letter-spacing: -0.05rem;
}

.sub-title {
    color: #4B5563;
    font-size: 1.1rem;
    text-align: center;
    margin-bottom: 2rem;
}

/* Cards for items */
.card {
    background-color: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

/* Info Banner styles */
.info-tag {
    background-color: #EFF6FF;
    border-left: 4px solid #3B82F6;
    color: #1E3A8A;
    padding: 0.75rem 1rem;
    border-radius: 0 8px 8px 0;
    margin-bottom: 1.5rem;
    font-size: 0.9rem;
}

/* Stylish section headers */
.section-header {
    font-size: 1.3rem;
    font-weight: 700;
    color: #111827;
    margin-top: 1.5rem;
    margin-bottom: 0.75rem;
    border-bottom: 2px solid #E5E7EB;
    padding-bottom: 0.25rem;
}
</style>
""", unsafe_allow_html=True)

# Title Header
st.markdown('<div class="gradient-title">📄 Resume-as-Code Web Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Design, live-preview, and compile a single-page ATS-friendly PDF instantly!</div>', unsafe_allow_html=True)

# ----------------- SESSION STATE & INITIAL DATA LOAD -----------------
if "resume_data" not in st.session_state:
    try:
        # Load from default file in the workspace
        if os.path.exists("resume.json"):
            with open("resume.json", "r", encoding="utf-8") as f:
                st.session_state.resume_data = json.load(f)
        else:
            raise FileNotFoundError()
    except Exception:
        # Fallback default resume structure
        st.session_state.resume_data = {
            "personal": {
                "name": "SEJAL BHAGAT",
                "location": "Nagpur, India",
                "phone": "+91 9022644273",
                "email": "bhagatsejal08@gmail.com",
                "linkedin": {
                    "display": "linkedin/Sejal-Bhagat",
                    "url": "https://linkedin.com/in/Sejal-Bhagat"
                },
                "github": {
                    "display": "github.com/SejalBhagat03",
                    "url": "https://github.com/SejalBhagat03"
                }
            },
            "summary": "Final-year Computer Science Engineering student with full-stack development experience...",
            "experience": [],
            "projects": [],
            "technical_skills": {
                "Programming": "C++, Python, JavaScript",
                "Frontend": "HTML, CSS, React.js"
            },
            "achievements": [],
            "education": [],
            "position_of_responsibility": []
        }

# Helper to trigger reruns
def trigger_rerun():
    st.rerun()

# ----------------- SIDEBAR CONTROLS -----------------
with st.sidebar:
    st.markdown("### 📤 Import & Export Config")
    st.markdown('<div class="info-tag">You can upload a <b>resume.json</b> file to populate this editor, or download your edits back to a JSON file.</div>', unsafe_allow_html=True)
    
    # JSON File Uploader
    uploaded_file = st.file_uploader("Upload resume.json", type=["json"])
    if uploaded_file is not None:
        try:
            uploaded_data = json.load(uploaded_file)
            st.session_state.resume_data = uploaded_data
            st.success("Config imported successfully!")
        except Exception as e:
            st.error(f"Error reading JSON: {e}")
            
    st.markdown("---")
    st.markdown("### 💾 Export Data")
    
    # Download JSON button
    json_bytes = json.dumps(st.session_state.resume_data, indent=2).encode('utf-8')
    st.download_button(
        label="📥 Download resume.json",
        data=json_bytes,
        file_name="resume.json",
        mime="application/json",
        use_container_width=True
    )
    
    st.markdown("---")
    st.markdown("### 💡 Quick Tips")
    st.markdown(
        """
        - **Keep it to 1 Page:** Standard resumes must fit on one page. The compiler will warn you if it runs over!
        - **ATS Compliance:** Helvetica standard font is used. Email, LinkedIn, and GitHub links are fully interactive.
        """
    )

# ----------------- LAYOUT: Editor (Left) & Preview (Right) -----------------
col_editor, col_preview = st.columns([1.1, 0.9])

# Current session state shortcut
data = st.session_state.resume_data

with col_editor:
    st.markdown('<div class="section-header">✏️ Resume Workspace Editor</div>', unsafe_allow_html=True)
    
    # Main Tabs
    tab_form, tab_json, tab_deploy = st.tabs(["📝 Form Editor", "⚙️ Edit Raw JSON", "🚀 Share & Host"])
    
    with tab_form:
        # --- PERSONAL INFORMATION ---
        with st.expander("👤 Personal Info & Contact", expanded=True):
            p_data = data.setdefault("personal", {})
            col_name, col_loc = st.columns(2)
            with col_name:
                p_data["name"] = st.text_input("Full Name", p_data.get("name", ""))
                p_data["email"] = st.text_input("Email Address", p_data.get("email", ""))
            with col_loc:
                p_data["location"] = st.text_input("Location (City, Country)", p_data.get("location", ""))
                p_data["phone"] = st.text_input("Phone Number", p_data.get("phone", ""))
                
            st.markdown("##### Social Links")
            col_li_disp, col_li_url = st.columns(2)
            li_data = p_data.setdefault("linkedin", {})
            with col_li_disp:
                li_data["display"] = st.text_input("LinkedIn Label", li_data.get("display", ""))
            with col_li_url:
                li_data["url"] = st.text_input("LinkedIn URL", li_data.get("url", ""))
                
            col_gh_disp, col_gh_url = st.columns(2)
            gh_data = p_data.setdefault("github", {})
            with col_gh_disp:
                gh_data["display"] = st.text_input("GitHub Label", gh_data.get("display", ""))
            with col_gh_url:
                gh_data["url"] = st.text_input("GitHub URL", gh_data.get("url", ""))

        # --- SUMMARY ---
        with st.expander("📝 Professional Summary", expanded=False):
            data["summary"] = st.text_area(
                "Short summary of your career focus and core value",
                data.get("summary", ""),
                height=100
            )

        # --- EXPERIENCE ---
        with st.expander("💼 Professional Experience", expanded=False):
            exp_list = data.setdefault("experience", [])
            updated_exp = []
            
            for idx, exp in enumerate(exp_list):
                st.markdown(f"**Job #{idx+1}**")
                col_r, col_c = st.columns(2)
                with col_r:
                    role = st.text_input("Role / Title", exp.get("role", ""), key=f"exp_role_{idx}")
                    company = st.text_input("Company Name", exp.get("company", ""), key=f"exp_company_{idx}")
                with col_c:
                    location = st.text_input("Location", exp.get("location", ""), key=f"exp_location_{idx}")
                    period = st.text_input("Period (e.g., Dec 2025–Present)", exp.get("period", ""), key=f"exp_period_{idx}")
                    
                techs = st.text_input("Technologies (comma-separated)", exp.get("technologies", ""), key=f"exp_techs_{idx}")
                
                bullets_str = "\n".join(exp.get("bullets", []))
                bullets_text = st.text_area("Bullets (one per line)", bullets_str, key=f"exp_bullets_{idx}", height=100)
                bullets = [b.strip() for b in bullets_text.split("\n") if b.strip()]
                
                updated_exp.append({
                    "role": role,
                    "company": company,
                    "location": location,
                    "period": period,
                    "technologies": techs,
                    "bullets": bullets
                })
                
                if st.button(f"🗑️ Remove Job #{idx+1}", key=f"remove_exp_{idx}"):
                    exp_list.pop(idx)
                    data["experience"] = exp_list
                    trigger_rerun()
                st.markdown("---")
                
            data["experience"] = updated_exp
            
            if st.button("➕ Add Job Experience"):
                exp_list.append({"role": "", "company": "", "location": "", "period": "", "technologies": "", "bullets": []})
                data["experience"] = exp_list
                trigger_rerun()

        # --- PROJECTS ---
        with st.expander("🚀 Projects", expanded=False):
            proj_list = data.setdefault("projects", [])
            updated_proj = []
            
            for idx, proj in enumerate(proj_list):
                st.markdown(f"**Project #{idx+1}**")
                col_pt, col_pd = st.columns(2)
                with col_pt:
                    title = st.text_input("Project Title", proj.get("title", ""), key=f"proj_title_{idx}")
                    link = st.text_input("GitHub / Demo Link", proj.get("link", ""), key=f"proj_link_{idx}")
                with col_pd:
                    tools = st.text_input("Tools/Tech Stack", proj.get("tools", ""), key=f"proj_tools_{idx}")
                    date = st.text_input("Date (e.g. Dec 2025)", proj.get("date", ""), key=f"proj_date_{idx}")
                    
                bullets_str = "\n".join(proj.get("bullets", []))
                bullets_text = st.text_area("Bullets (one per line)", bullets_str, key=f"proj_bullets_{idx}", height=100)
                bullets = [b.strip() for b in bullets_text.split("\n") if b.strip()]
                
                updated_proj.append({
                    "title": title,
                    "link": link,
                    "date": date,
                    "tools": tools,
                    "bullets": bullets
                })
                
                if st.button(f"🗑️ Remove Project #{idx+1}", key=f"remove_proj_{idx}"):
                    proj_list.pop(idx)
                    data["projects"] = proj_list
                    trigger_rerun()
                st.markdown("---")
                
            data["projects"] = updated_proj
            
            if st.button("➕ Add Project"):
                proj_list.append({"title": "", "link": "", "date": "", "tools": "", "bullets": []})
                data["projects"] = proj_list
                trigger_rerun()

        # --- TECHNICAL SKILLS ---
        with st.expander("🛠️ Technical Skills", expanded=False):
            skills = data.setdefault("technical_skills", {})
            updated_skills = {}
            
            # Allow key-value addition
            keys = list(skills.keys())
            for idx, key in enumerate(keys):
                col_k, col_v = st.columns([0.3, 0.7])
                with col_k:
                    # Input for the Skill Category Name (e.g., Programming)
                    new_key = st.text_input("Category", key, key=f"skill_key_{idx}")
                with col_v:
                    # Input for the values (e.g., C++, Python)
                    val = st.text_input("Skills List", skills.get(key, ""), key=f"skill_val_{idx}")
                
                if new_key:
                    updated_skills[new_key] = val
                    
                if st.button(f"🗑️ Remove Category: {key}", key=f"remove_skill_{idx}"):
                    skills.pop(key, None)
                    data["technical_skills"] = skills
                    trigger_rerun()
                st.markdown(" ")
            
            data["technical_skills"] = updated_skills
            
            # Form to add a new category
            st.markdown("**Add New Skill Category**")
            col_add_k, col_add_v = st.columns([0.4, 0.6])
            with col_add_k:
                new_cat_name = st.text_input("New Category Name", "", key="new_skill_cat")
            with col_add_v:
                new_cat_vals = st.text_input("New Skills List", "", key="new_skill_val")
                
            if st.button("➕ Add Skill Category"):
                if new_cat_name.strip():
                    skills[new_cat_name.strip()] = new_cat_vals
                    data["technical_skills"] = skills
                    trigger_rerun()
                else:
                    st.warning("Please enter a category name.")

        # --- ACHIEVEMENTS ---
        with st.expander("🏆 Achievements", expanded=False):
            ach_list = data.setdefault("achievements", [])
            ach_str = "\n".join(ach_list)
            ach_text = st.text_area("Achievements (one per line, HTML tags like <b>bold</b> are supported)", ach_str, height=120)
            data["achievements"] = [a.strip() for a in ach_text.split("\n") if a.strip()]

        # --- EDUCATION ---
        with st.expander("🎓 Education", expanded=False):
            edu_list = data.setdefault("education", [])
            updated_edu = []
            
            for idx, edu in enumerate(edu_list):
                st.markdown(f"**Degree/Education #{idx+1}**")
                col_d, col_i = st.columns(2)
                with col_d:
                    degree = st.text_input("Degree / Qualification", edu.get("degree", ""), key=f"edu_deg_{idx}")
                    details = st.text_input("Grade / Extra Info (e.g. CGPA: 9.1 / 10)", edu.get("details", ""), key=f"edu_details_{idx}")
                with col_i:
                    institution = st.text_input("Institution", edu.get("institution", ""), key=f"edu_inst_{idx}")
                    period = st.text_input("Graduation Date / Period", edu.get("period", ""), key=f"edu_period_{idx}")
                    
                updated_edu.append({
                    "degree": degree,
                    "institution": institution,
                    "details": details,
                    "period": period
                })
                
                if st.button(f"🗑️ Remove Education #{idx+1}", key=f"remove_edu_{idx}"):
                    edu_list.pop(idx)
                    data["education"] = edu_list
                    trigger_rerun()
                st.markdown("---")
                
            data["education"] = updated_edu
            
            if st.button("➕ Add Education Item"):
                edu_list.append({"degree": "", "institution": "", "details": "", "period": ""})
                data["education"] = edu_list
                trigger_rerun()

        # --- POSITIONS OF RESPONSIBILITY ---
        with st.expander("🤝 Positions of Responsibility", expanded=False):
            por_list = data.setdefault("position_of_responsibility", [])
            updated_por = []
            
            for idx, por in enumerate(por_list):
                st.markdown(f"**Position #{idx+1}**")
                col_pr, col_pp = st.columns([0.7, 0.3])
                with col_pr:
                    role = st.text_input("Role & Club/Event (e.g. Technical Secretary, Club)", por.get("role", ""), key=f"por_role_{idx}")
                with col_pp:
                    period = st.text_input("Period (Optional)", por.get("period", ""), key=f"por_period_{idx}")
                    
                bullets_str = "\n".join(por.get("bullets", []))
                bullets_text = st.text_area("Bullets (one per line)", bullets_str, key=f"por_bullets_{idx}", height=80)
                bullets = [b.strip() for b in bullets_text.split("\n") if b.strip()]
                
                updated_por.append({
                    "role": role,
                    "period": period,
                    "bullets": bullets
                })
                
                if st.button(f"🗑️ Remove Position #{idx+1}", key=f"remove_por_{idx}"):
                    por_list.pop(idx)
                    data["position_of_responsibility"] = por_list
                    trigger_rerun()
                st.markdown("---")
                
            data["position_of_responsibility"] = updated_por
            
            if st.button("➕ Add Position of Responsibility"):
                por_list.append({"role": "", "period": "", "bullets": []})
                data["position_of_responsibility"] = por_list
                trigger_rerun()

    # --- ADVANCED JSON EDITOR ---
    with tab_json:
        st.markdown('<div class="info-tag">You can directly write or edit the raw JSON text below. Click <b>"Apply Changes"</b> to synchronize the form and layout preview.</div>', unsafe_allow_html=True)
        json_string = json.dumps(data, indent=2)
        edited_json = st.text_area("Raw JSON Editor", json_string, height=500)
        
        if st.button("⚙️ Apply JSON Changes", use_container_width=True):
            try:
                st.session_state.resume_data = json.loads(edited_json)
                st.success("JSON Configuration applied successfully!")
                trigger_rerun()
            except Exception as e:
                st.error(f"Invalid JSON Format: {e}")

    # --- DEPLOYMENT / SHARING INSTRUCTIONS ---
    with tab_deploy:
        st.subheader("🌐 Share your resume builder with the world!")
        st.markdown(
            """
            This application is ready to be shared with friends, classmates, or colleagues. They can visit your site, enter their details, and download their own PDF resume without writing any code.
            
            ### 🚀 How to Host Online for FREE (in 3 steps):
            
            1. **Push your code to GitHub:**
               Make sure this folder is pushed to a repository on your GitHub account.
            2. **Log into Streamlit Community Cloud:**
               Go to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
            3. **Deploy in 1 Click:**
               Click **"Create app"**, select your repository, select the branch (`main` or `master`), set the Main File Path to `app.py`, and click **"Deploy!"**
            
            Your app will be live at a public URL (e.g. `https://yourname-resume-generator.streamlit.app`)!
            """
        )

# ----------------- PDF PREVIEW & GENERATION PANEL (RIGHT) -----------------
with col_preview:
    st.markdown('<div class="section-header">📄 PDF Live Compiler</div>', unsafe_allow_html=True)
    
    # Check if a compilation has occurred already
    pdf_filename = "Generated_Resume.pdf"
    
    st.markdown('<div class="info-tag">Click the button below to compile the JSON config into the final styled PDF.</div>', unsafe_allow_html=True)
    
    compile_btn = st.button("🚀 Compile & Preview PDF", use_container_width=True)
    
    # We want to compile initially or on button click
    compile_status = False
    warning_msg = None
    
    if compile_btn or os.path.exists(pdf_filename):
        with st.spinner("Compiling PDF..."):
            success, msg = generate_pdf(data, pdf_filename)
            compile_status = success
            warning_msg = msg
            
        if compile_status:
            if warning_msg:
                st.warning(f"⚠️ {warning_msg}")
            else:
                st.success("✅ Resume compiled successfully (exactly 1 page limit check passed)!")
                
            # Download PDF button
            with open(pdf_filename, "rb") as pdf_file:
                pdf_bytes = pdf_file.read()
                
            st.download_button(
                label="📥 Download Compiled PDF",
                data=pdf_bytes,
                file_name="Sejal_Bhagat_Resume.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
            st.markdown("---")
            st.markdown("#### Preview Pane")
            
            # Embed PDF using base64 iframe
            try:
                base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                pdf_iframe = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" style="border:1px solid #E5E7EB; border-radius:8px;"></iframe>'
                st.markdown(pdf_iframe, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Could not render PDF preview in browser: {e}")
        else:
            st.error(f"❌ Failed to compile PDF: {msg}")
    else:
        st.info("Click 'Compile & Preview PDF' to see the layout here.")
