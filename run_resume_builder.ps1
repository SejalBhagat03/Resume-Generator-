# PowerShell wrapper to silence Streamlit's missing ScriptRunContext warning
$env:SCRIPT_RUN_CONTEXT = "1"
python -m resume_builder.app
