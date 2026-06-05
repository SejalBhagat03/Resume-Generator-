# 🐛 Bugs & Fixes Log — Resume Builder Pro

> Every bug we encountered and exactly how we fixed it.
> Organized by date. Most recent at top.

---

## 📅 June 5, 2026

---

### Bug #1 — "Add to Resume" Button Was Not Visible in GitHub Tab

**Symptom:** You could see GitHub repos listed, but there was no button to add them to your resume.

**Root Cause:**
- `github_username` was stored in `st.session_state` which resets every time you restart the app
- So on every restart, the tab showed "Please enter a username" — empty, no repos, no buttons
- Even when username was entered, the button rendering had layout issues inside collapsed expanders

**Fix Applied:**
- Saved username to a JSON file: `resume_builder/data/github_config.json`
- Added a manual **🔍 Load Repos** button so repos only fetch when clicked (not on every rerun)
- Changed the Add button to a prominent **purple primary button** on the right of each card
- Repos already in resume show **✅ Added** badge instead — you can't add twice

**Files Changed:**
- `resume_builder/career_dashboard.py` — full rewrite of the GitHub Evidence tab (lines 273–420)
- `resume_builder/data/github_config.json` — new file created automatically

---

### Bug #2 — Duplicate Project Added to Resume

**Symptom:** Clicking "Add to Resume" twice for the same repo added the project twice to your PDF.

**Root Cause:**
- No duplicate check existed — the button blindly appended to the projects list every time clicked

**Fix Applied:**
```python
# Before adding, check if title already exists
existing_titles = [p.get("title", "").lower() for p in resume["projects"]]
already_added = proj["name"].lower() in existing_titles

if already_added:
    st.success("✅ Added")   # show green badge, no button
else:
    st.button("➕ Add to Resume")   # show button only if not present
```

**Files Changed:**
- `resume_builder/career_dashboard.py` — add-button block (around line 383–420)

**Also:** The duplicate in the live session was cleared by pressing `Ctrl+Shift+R` (hard refresh) in browser.

---

### Bug #3 — Skill Match Section Disappeared from GitHub Tab

**Symptom:** The 🛠️ Skill Match section (green/yellow/red bars showing how much GitHub evidence you have for each skill) disappeared after a rewrite.

**Root Cause:**
- When rewriting the GitHub Evidence tab (Bug #1 fix), we replaced all the tab code
- The Skill Confidence Metrics section was in the original code but was not included in the new version

**Fix Applied:**
Restored the section with improved visual design — progress bars instead of plain text:
```python
for skill in evidence:
    # Colored progress bar per skill
    st.markdown(f'<div style="..."><progress value="{confidence}"/></div>', unsafe_allow_html=True)
```

**Files Changed:**
- `resume_builder/career_dashboard.py` — inserted between score card and repos list (lines 338–377)

---

### Bug #4 — Code Changes Not Showing Instantly (Hot Reload Broken)

**Symptom:** Every code change required manually killing and restarting the app. Streamlit's auto-reload wasn't working.

**Root Cause:**
```python
# root app.py used this:
runpy.run_path("resume_builder/app.py")
```
`runpy` bypasses Python's import system. Streamlit watches imported modules for changes — since `runpy` doesn't register the file as an import, Streamlit had no idea `career_dashboard.py` or `app.py` existed and never watched them.

**Fix Applied:**
Added to `.streamlit/config.toml`:
```toml
[server]
fileWatcherType = "poll"   # actively check files every second
```

**Permanent Fix (use when actively developing):**
```bash
# Run directly instead of through wrapper
python -m streamlit run resume_builder\app.py
```
This makes Streamlit natively watch all files in `resume_builder/`.

**Files Changed:**
- `.streamlit/config.toml` — added `[server]` section

---

### Bug #5 — Website Went Completely Blank

**Symptom:** The browser showed a completely white/empty page at localhost:8501. No error shown, just nothing.

**Root Cause:**
While trying to fix Bug #4, changed `app.py` from `runpy` to a regular Python import:
```python
# This BROKE the app:
from resume_builder import app  # ← caused blank page
```

Streamlit apps run all their code at **module level** (not inside a `main()` function). When Python `import`s a module, it executes that module-level code before Streamlit's session is ready → all `st.button()`, `st.markdown()` calls fire with no active Streamlit context → silent failure → blank page.

**Fix Applied:**
Immediately reverted to the safe `runpy` approach:
```python
# Safe — correct way:
import runpy
runpy.run_path("resume_builder/app.py", run_name="__main__")
```

> **Rule:** Never use `import` to load a Streamlit app module. Always use `runpy.run_path()`.

**Files Changed:**
- `app.py` — reverted to runpy approach

---

### Bug #6 — Deprecated API Warnings Flooding the Console

**Symptom:** Server log flooded with:
```
Please replace st.components.v1.html with st.iframe.
st.components.v1.html will be removed after 2026-06-01.
```

**Root Cause:**
Two places in code used an old Streamlit API that was officially removed:
1. `app.py` — used for injecting keyboard shortcut JavaScript (Ctrl+Z, Ctrl+Y, Ctrl+S)
2. `career_dashboard.py` — used for rendering the Knowledge Graph visualization

**Fix Applied:**
- **`app.py`** keyboard shortcuts:
  ```python
  # Old (broken):
  st.components.v1.html("<script>...</script>", height=0, width=0)
  
  # New (correct):
  st.markdown("<script>...</script>", unsafe_allow_html=True)
  ```

- **`career_dashboard.py`** knowledge graph:
  ```python
  # Old (broken):
  st.components.v1.html(graph_html, height=500)
  
  # New (correct):
  import streamlit.components.v1 as components
  components.html(graph_html, height=500, scrolling=True)
  ```

**Files Changed:**
- `resume_builder/app.py` — line ~1387
- `resume_builder/career_dashboard.py` — line ~364

---

### Bug #7 — Streamlit Cloud Showing White/Invisible Text

**Symptom:** The deployed website at `https://resumesgenerator.streamlit.app` showed:
- Career Center heading was faint / invisible
- Dropdown had red border
- Most text was hard or impossible to read
- But `localhost:8501` looked perfectly fine

**Root Cause — TWO separate issues:**

**Issue A: `.streamlit/` was in `.gitignore`**
```
# .gitignore had this line:
.streamlit/   ← blocks ENTIRE folder from being pushed to GitHub
```
So Streamlit Cloud never received `config.toml`. It used its own default dark mode instead of the light purple theme.

**Issue B: No global text color in CSS**
```css
/* Only background was set, text color was missing: */
html, body { background: #F0F2F8; }
/* ← no color: property! */
```
On Streamlit Cloud (dark mode default), text defaults to white → white text on light background → invisible.

**Fix Applied:**

1. Fixed `.gitignore` — keep only secrets out:
```
# Before:
.streamlit/

# After:
.streamlit/secrets.toml    ← only secrets file excluded, config.toml is now tracked
```

2. Added global text color to CSS:
```css
html, body, [data-testid="stAppViewContainer"] {
  background: #F0F2F8 !important;
  color: #1E293B !important;   /* ← this was the missing line */
}
p, h1, h2, h3, span, div { color: #1E293B; }
```

**Files Changed:**
- `.gitignore` — removed `.streamlit/`, added `.streamlit/secrets.toml`
- `.streamlit/config.toml` — now tracked by Git (new file on GitHub)
- `resume_builder/app.py` — added `color: #1E293B` to base CSS

---

### Bug #8 — "Who Is actions-user Committing to My Repo?!" (Not Actually a Bug)

**Symptom:** GitHub showed a commit from user `actions-user` with message:
```
chore(pdf): auto-compile latest resume PDF [skip ci]
```
Appeared to be an unauthorized commit from an unknown person.

**Root Cause:**
This was NOT a bug. It was the GitHub Actions workflow (`.github/workflows/compile_resume.yml`) working exactly as designed:
- Triggers on every push to `resume.json`
- GitHub's cloud server runs Python, generates `Sejal_Bhagat_Resume.pdf`
- Commits the PDF back using GitHub's system bot account `actions-user`
- `[skip ci]` prevents infinite loop (bot's commit doesn't trigger another run)

**Resolution:** No fix needed — explained to user that this is their own automation working correctly. ✅

---

### Bug #9 — Git Push Rejected: "Remote Has Work You Don't Have"

**Symptom:**
```
! [rejected] main -> main (fetch first)
error: failed to push some refs
hint: Updates were rejected because the remote contains work you do not have locally
```

**Root Cause:**
Git timeline collision:
1. We committed locally
2. GitHub Actions bot also committed (PDF generation) to the remote
3. Remote history diverged from local → Git refuses to push

```
Local:  A → B → C (our fix)
Remote: A → B → D (bot PDF commit)  ← Git sees these as two different paths
```

**Fix Applied:**
```bash
git fetch origin          # download remote's state without merging
git merge origin/main     # combine bot's commit with ours
git push origin main      # now histories are aligned → push succeeds
```

**Files Changed:**
- None — just a git operation to synchronize histories

---

## 📊 Quick Reference Table

| # | Bug | File(s) Affected | Fix Type |
|---|-----|-----------------|----------|
| 1 | Add to Resume button missing | `career_dashboard.py` | Feature rewrite |
| 2 | Duplicate project added | `career_dashboard.py` | Add duplicate check |
| 3 | Skill Match section missing | `career_dashboard.py` | Restore deleted code |
| 4 | Hot reload broken | `.streamlit/config.toml` | Config change |
| 5 | Blank white page | `app.py` | Revert import method |
| 6 | Deprecated API warnings | `app.py`, `career_dashboard.py` | Update API calls |
| 7 | Cloud colors broken | `.gitignore`, `app.py`, `config.toml` | Track config in Git + add CSS color |
| 8 | Unknown committer scare | — | Education (not a bug) |
| 9 | Git push rejected | — | Git fetch + merge |
