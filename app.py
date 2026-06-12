import sys
import os

# Add the resume_builder folder to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "resume_builder")))

# Import and execute resume_builder/app.py
import app
