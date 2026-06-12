"""Firestore Synchronization Service Placeholder.

This module provides stubs for synchronizing resumes to/from Cloud Firestore.
"""

import streamlit as st

def sync_resume_to_firestore(resume_data: dict) -> bool:
    """Sync local resume data to Firestore."""
    st.info("Firestore Sync: Feature not configured.")
    return False

def fetch_resumes_from_firestore() -> list:
    """Fetch all resumes from Firestore for the active user."""
    return []
