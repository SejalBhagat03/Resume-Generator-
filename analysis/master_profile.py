import os
import json
import copy

# Absolute paths determined from this file's position
ANALYSIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(ANALYSIS_DIR)
BUILDER_DIR = os.path.join(PROJECT_ROOT, "resume_builder")

MASTER_PROFILE_PATH = os.path.join(PROJECT_ROOT, "exports", "json", "master_profile.json")
VERSIONS_DIR = os.path.join(PROJECT_ROOT, "exports", "json", "resume_versions")

# Common fields inherited from Master Profile
MASTER_KEYS = ["personal", "education", "technical_skills", "achievements", "certifications", "position_of_responsibility"]

def ensure_setup(active_resume_data: dict):
    """Ensure master_profile.json and versions directory exist."""
    os.makedirs(VERSIONS_DIR, exist_ok=True)
    os.makedirs(os.path.join(BUILDER_DIR, "data"), exist_ok=True)
    
    # Bootstrap master profile if missing
    if not os.path.exists(MASTER_PROFILE_PATH):
        master_data = {}
        for key in MASTER_KEYS:
            master_data[key] = copy.deepcopy(active_resume_data.get(key, {} if key in ["personal", "technical_skills"] else []))
        save_master_profile(master_data)

def load_master_profile() -> dict:
    """Load the master profile data."""
    if os.path.exists(MASTER_PROFILE_PATH):
        try:
            with open(MASTER_PROFILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_master_profile(data: dict):
    """Save master profile data to disk."""
    clean_data = {}
    for key in MASTER_KEYS:
        clean_data[key] = data.get(key, {} if key in ["personal", "technical_skills"] else [])
    with open(MASTER_PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(clean_data, f, indent=2)

def list_versions() -> list:
    """List all saved resume versions (file basenames without extension)."""
    if not os.path.exists(VERSIONS_DIR):
        return []
    return [os.path.splitext(f)[0] for f in os.listdir(VERSIONS_DIR) if f.endswith(".json")]

def load_version(name: str) -> dict:
    """Load a specific resume version and merge it with master profile inheritance."""
    version_path = os.path.join(VERSIONS_DIR, f"{name}.json")
    if not os.path.exists(version_path):
        return {}
        
    try:
        with open(version_path, "r", encoding="utf-8") as f:
            version_data = json.load(f)
    except Exception:
        return {}
        
    # Merge master profile common fields onto the loaded version (Inheritance)
    master = load_master_profile()
    for key in MASTER_KEYS:
        if key in master:
            version_data[key] = copy.deepcopy(master[key])
            
    return version_data

def save_version(name: str, data: dict):
    """Save a resume version to disk (storing it completely)."""
    os.makedirs(VERSIONS_DIR, exist_ok=True)
    version_path = os.path.join(VERSIONS_DIR, f"{name}.json")
    with open(version_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def update_resume_with_master(resume_data: dict) -> dict:
    """Inject master profile values into a resume dataset."""
    master = load_master_profile()
    updated = copy.deepcopy(resume_data)
    for key in MASTER_KEYS:
        if key in master:
            updated[key] = copy.deepcopy(master[key])
    return updated

def save_active_resume_and_sync(resume_data: dict, active_version_name: str = None):
    """
    Save the edited active resume.
    If fields in MASTER_KEYS have changed, update master_profile.json
    and optionally propagate to all version files.
    """
    # 1. Update master profile with active values
    master = load_master_profile()
    master_changed = False
    for key in MASTER_KEYS:
        if key in resume_data:
            if master.get(key) != resume_data[key]:
                master[key] = copy.deepcopy(resume_data[key])
                master_changed = True
                
    if master_changed:
        save_master_profile(master)
        # 2. Propagate updates to all other stored versions
        for ver_name in list_versions():
            # If we are working on a version, skip saving it here as we will save it actively
            if active_version_name and ver_name == active_version_name:
                continue
            ver_data = load_version(ver_name)  # load_version automatically merges master
            save_version(ver_name, ver_data)
            
    # 3. Save active version if specified
    if active_version_name:
        save_version(active_version_name, resume_data)
