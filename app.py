import os
import sys
import runpy

# Ensure project root is on Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Run the main app module
app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resume_builder", "app.py")
runpy.run_path(app_path, run_name="__main__")
