# Wrapper that re-exports the full GitHubIntegration implementation
from analysis.github_integration import GitHubIntegration as _RealGitHubIntegration

class GitHubIntegration(_RealGitHubIntegration):
    """Thin wrapper to expose the full implementation under services.github_service.

    All methods (fetch_repos, analyze_profile, etc.) are inherited from the real
    implementation located in `analysis/github_integration.py`. This keeps the
    test import path (`services.github_service.GitHubIntegration`) functional
    without duplicating logic.
    """
    pass
