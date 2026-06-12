import os
import sys
import importlib.util

# Ensure project root is on Python path so all resume_builder imports work
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Load resume_builder/app.py as a named module.
# Using importlib (instead of runpy) registers the file in sys.modules,
# which allows Streamlit's file watcher to detect changes and hot-reload.
_APP_PATH = os.path.join(PROJECT_ROOT, "resume_builder", "app.py")
_spec = importlib.util.spec_from_file_location("resume_builder.app", _APP_PATH)
_module = importlib.util.module_from_spec(_spec)
sys.modules["resume_builder.app"] = _module
_spec.loader.exec_module(_module)
