# 🚀 How To Run — Resume Builder Pro

## Prerequisites (One-Time Setup)

Make sure you have these installed:
- **Python 3.10+** — check with `python --version`
- **Git** — check with `git --version`

---

## Step 1 — Clone The Project (First Time Only)

```bash
git clone https://github.com/SejalBhagat03/Resume-Generator-.git
cd Resume-Generator-
```

---

## Step 2 — Create Virtual Environment (First Time Only)

```bash
# Create the virtual environment
python -m venv .venv

# Activate it (Windows)
.venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
```

---

## Step 3 — Run The App

### Option A — The Double-Click Launcher (Windows Only — Easiest! 🚀)
Simply double-click the `run.bat` file in the root directory!
* It will check if Python is installed.
* Set up a virtual environment and download dependencies automatically.
* Start the Streamlit app and open it in your browser immediately.

---

### Option B — Standard CLI Run
```bash
python -m streamlit run app.py
```
Then open: **http://localhost:8501**

---

### Option C — Full Hot Reload (Recommended for Core Development)
```bash
python -m streamlit run resume_builder\app.py
```
> ✅ This way, Streamlit watches ALL files in `resume_builder/` — any change you make shows up instantly in the browser without restarting.

---

## ⚠️ Common Problems When Starting

### Problem: "ModuleNotFoundError: No module named 'streamlit'"
```bash
# You forgot to activate the virtual environment!
.venv\Scripts\activate
```

### Problem: "Port 8501 already in use"
```bash
# Kill all Python processes and retry
taskkill /F /IM python.exe
python -m streamlit run app.py
```

### Problem: Changes I made don't show up in the browser
```bash
# Option 1: Hard refresh the browser
Ctrl + Shift + R

# Option 2: Restart the server (kill + rerun)
Ctrl+C   (stop server)
python -m streamlit run app.py

# Option 3: Clear Python cache files
Get-ChildItem -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force
python -m streamlit run app.py
```

### Problem: Website is blank / white page
The `app.py` root file uses `runpy.run_path()` — **never change this to `import`**.
If you accidentally did, revert `app.py` to:
```python
import os, sys, runpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "resume_builder", "app.py"), run_name="__main__")
```

---

## Pushing Changes to GitHub

```bash
git add .
git commit -m "your message here"
git pull --rebase    # always pull first in case the PDF bot committed
git push
```

> After pushing, the **GitHub Actions bot** will automatically compile your PDF and commit it.
> This is normal — you'll see "actions-user" commit in your repo history.

---

## Streamlit Cloud Deployment

The app is deployed at: **https://resumesgenerator.streamlit.app**

Streamlit Cloud watches your GitHub `main` branch and **auto-redeploys** every time you push.

### ⚠️ Important Rules for Cloud Deployment

1. **`.streamlit/config.toml` must be in Git** — this file controls colors and theme. It was accidentally in `.gitignore` before (now fixed). If you ever recreate the `.gitignore`, do NOT add `.streamlit/` to it.

2. **`.streamlit/secrets.toml` must NOT be in Git** — this file would contain API keys if you add any. It's excluded in `.gitignore` for security.

3. After pushing, wait **2–3 minutes** for Streamlit Cloud to redeploy. Then hard-refresh the cloud URL.

---

## Key Files You Should Know

| File | What To Edit It For |
|------|-------------------|
| `resume.json` | Your actual resume content — name, experience, projects, skills |
| `.streamlit/config.toml` | Change app colors, theme |
| `resume_builder/templates/sejal_original/template.py` | Change how the PDF looks |
| `.github/workflows/compile_resume.yml` | Change when/how the PDF auto-generates |
