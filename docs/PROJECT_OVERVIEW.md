# 🏗️ Project Overview — Resume Builder Pro

## What Is This App?

**Resume Builder Pro** is a smart, AI-powered resume builder built with Python and Streamlit. Instead of using a Word doc or Canva, you:

1. Fill in your details in a structured form (left panel)
2. See a **live PDF preview** update in real time (right panel)
3. Download the final professional PDF

It also connects to your **GitHub profile** to automatically suggest projects to add to your resume.

---

## 🧱 How The App Is Built

```
resume-generator/
│
├── app.py                          ← Entry point — Streamlit runs this
│
├── resume_builder/                 ← ALL the main app code lives here
│   ├── app.py                      ← Main Streamlit app (editor, layout, CSS)
│   ├── career_dashboard.py         ← Career Center page (GitHub, skills, etc.)
│   │
│   ├── templates/                  ← Resume PDF visual templates
│   │   ├── sejal_original/         ← Your custom template (the one you use)
│   │   ├── modern/
│   │   ├── minimal/
│   │   ├── ats/                    ← ATS-friendly simple format
│   │   └── creative/
│   │
│   ├── generators/
│   │   └── pdf_generator.py        ← Converts your JSON data → PDF file
│   │
│   ├── utils/                      ← Smart AI tools
│   │   ├── github_integration.py   ← Fetches your GitHub repos
│   │   ├── evidence_system.py      ← Matches GitHub to resume skills
│   │   ├── achievement_quantifier.py ← Suggests better bullet points
│   │   ├── consistency_checker.py  ← Finds mistakes/inconsistencies
│   │   ├── gap_analyzer.py         ← Career gap analysis
│   │   ├── interview_prep.py       ← Interview question generator
│   │   ├── knowledge_graph.py      ← Visual skill ↔ project mapping
│   │   ├── master_profile.py       ← Workspace/version management
│   │   └── project_story.py        ← Converts project info to bullets
│   │
│   ├── parser/                     ← Reads/parses resume JSON
│   └── data/                       ← Runtime data files
│       ├── github_config.json      ← Saves your GitHub username
│       └── github_cache.json       ← Caches GitHub API results
│
├── resume.json                     ← YOUR resume data (the source of truth)
├── resume_versions/                ← Saved versions of your resume
│
├── .streamlit/
│   └── config.toml                 ← App theme (colors, font) — MUST be in Git
│
├── .github/
│   └── workflows/
│       └── compile_resume.yml      ← Auto-generates PDF on every push
│
└── docs/                           ← 📚 This documentation folder
```

---

## 🔄 How Data Flows

```
You type in the form
        ↓
resume.json (the data file) gets updated in memory
        ↓
PDF generator reads the JSON + your chosen template
        ↓
Live PDF preview updates on the right side
        ↓
You click "Save to File" → resume.json saved to disk
        ↓
You do git push → GitHub Actions auto-generates PDF → uploads to GitHub
```

---

## 🎨 Key Design Decisions

| Decision | Why |
|----------|-----|
| **JSON as data format** | Easy to edit, version, and back up. Can open in any text editor. |
| **Template system** | Separates your data from how it looks. Swap templates without losing data. |
| **Streamlit framework** | Python-only, no JavaScript needed for the UI. Fast to build. |
| **GitHub Actions PDF bot** | Recruiters can always download the latest PDF from your repo |
| **Poll-based file watcher** | Windows doesn't always send file-change OS events reliably, so we poll every second |

---

## 🌐 Deployment

- **Local**: `http://localhost:8501`
- **Cloud**: `https://resumesgenerator.streamlit.app` (Streamlit Community Cloud — free hosting)
- **GitHub repo**: `https://github.com/SejalBhagat03/Resume-Generator-`
