import sys
import os
import copy
import json

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock streamlit session state
import streamlit as st

class MockSessionState(dict):
    def __getattr__(self, name):
        return self.get(name)
    def __setattr__(self, name, value):
        self[name] = value

with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resume.json"), "r", encoding="utf-8") as f:
    DEFAULT_RESUME = json.load(f)

st.session_state = MockSessionState({
    "resume": DEFAULT_RESUME,
    "career_active_tool": "github",
    "target_role": "Frontend Developer",
    "github_username": "SejalBhagat03",
    "active_version": "Default Workspace"
})

from resume_builder.career_dashboard import show_career_center

try:
    print("Testing show_career_center rendering...")
    show_career_center()
    print("SUCCESS: show_career_center completed without exceptions!")
except Exception as e:
    import traceback
    print("FAILURE: Exception encountered!")
    traceback.print_exc()
