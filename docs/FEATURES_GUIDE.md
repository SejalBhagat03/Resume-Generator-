# 📖 Features Guide — Resume Builder Pro

How to use every feature of the app.

---

## 🖥️ The Two Panels

When you open the app, you see two sides:

| Left Panel | Right Panel |
|-----------|-------------|
| **Editor** — where you fill in your info | **Live PDF Preview** — updates automatically |

---

## 📝 Editor Workspace Tabs

### 1. 👤 Personal Info
Fill in your name, email, phone, LinkedIn URL, GitHub URL.

> **Tip:** The "Label" field is what shows on the PDF (e.g. `linkedin/Sejal-Bhagat`) and the "URL" is the actual link.

---

### 2. 📋 Summary
A 40–80 word career summary. This appears at the top of your resume.

> **Tip:** Keep it to 2–3 sentences. Focus on your strongest skills and what kind of role you're targeting.

---

### 3. 💼 Experience
Add your internships and jobs here. Each entry has:
- **Role** — your job title
- **Company** — company name
- **Location** — city (e.g. "Nagpur, India")
- **Period** — date range (e.g. "Dec 2025–Present")
- **Technologies** — comma-separated tech stack
- **Bullets** — one achievement per line (start with action verbs!)

---

### 4. 🚀 Projects
Your personal/academic projects. Each has:
- **Title** — project name
- **Link** — GitHub URL (shows as clickable link in PDF)
- **Date** — when you built it (e.g. "Jul 2025")
- **Tools** — comma-separated tech stack
- **Bullets** — what you built and achieved

> **Tip:** Projects can be added automatically from GitHub! See the GitHub Evidence tab.

---

### 5. 🛠️ Skills
Technical skills organized by category. Edit the category names and values freely.

---

### 6. 🏆 Achievements
One achievement per line. Bold text using `<b>text</b>`.

Example:
```
<b>Academic Excellence:</b> Maintained a CGPA of 9.1/10 in B.Tech CSE.
```

---

### 7. 🎓 Education
Your degrees. Each has degree name, institution, details (CGPA/%), and year.

---

### 8. ⚙️ Settings
Control PDF layout:
- **Font Size** — make text bigger/smaller
- **Spacing** — add/remove whitespace between sections
- **Template** — choose a different visual design for your PDF

---

## 💼 Career Center

Access from the top bar dropdown → **Career Center**.

### Tab 1 — 👤 Master Profile Sync
Syncs your resume data with a "master profile" that stays consistent across multiple resume versions.

### Tab 2 — ✅ Consistency Checker
Scans your resume for:
- Date format mismatches
- Missing required fields
- Inconsistent terminology

### Tab 3 — 📊 Career Gap Analyzer
Analyzes your experience timeline and identifies skill gaps for your target roles.

### Tab 4 — ⚡ Achievement Quantifier
Takes your bullet points and suggests improved versions with numbers and metrics.

Example:
- Before: "Improved page load performance"
- After: "Achieved 30% improvement in page load performance through code optimization"

### Tab 5 — 🎤 Interview Prep Mode
Generates practice interview questions based on your resume content.

### Tab 6 — 🐙 GitHub Evidence (Most Used)
**This is the most powerful feature:**

1. Enter your GitHub username (saved automatically)
2. Click **🔍 Load Repos**
3. See all your public repositories
4. Click **➕ Add to Resume** on any project
5. It automatically fills in: title, link, date, tech stack, and a bullet point
6. You're taken back to the Editor with a green success banner

Also shows a **Skill Match** section — which of your resume skills have GitHub evidence (repos proving you actually used them).

### Tab 7 — 📝 Project Story Generator
Enter a project name + tech stack + short description → get a professionally worded bullet point list.

### Tab 8 — 🕸️ Knowledge Graph
Visual diagram showing which of your skills connect to which projects and experiences.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + Z` | Undo last change |
| `Ctrl + Y` | Redo |
| `Ctrl + Shift + Z` | Redo (alternative) |
| `Ctrl + S` | Save to file |

---

## 📥 Downloading Your Resume

Two buttons at the bottom of the right panel:
- **⬇️ Download PDF** — download the formatted PDF resume
- **⬇️ Download JSON** — download your data file (use for backups or sharing)

---

## 💾 Saving Versions

Top right of Career Center → type a version name → click **Save As Version**

Examples:
- `frontend_developer`
- `fullstack_v2`
- `internship_application`

Each version is saved as a separate JSON file in `resume_versions/`.

---

## 🚨 Things To Never Do

| Don't | Why |
|-------|-----|
| Change `app.py` root file to use `import` instead of `runpy` | Causes blank white page |
| Add `.streamlit/` back to `.gitignore` | Your theme won't work on Streamlit Cloud |
| Add `.streamlit/secrets.toml` to Git | That file would contain API keys — security risk |
| Click "Add to Resume" multiple times for same repo | Adds duplicates (though now blocked by duplicate check) |
