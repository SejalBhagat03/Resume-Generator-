import os
import sys
import json
import pytest

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.master_profile import (
    ensure_setup, load_master_profile, save_master_profile,
    list_versions, load_version, save_version, update_resume_with_master
)
from analysis.consistency_checker import ConsistencyChecker
from analysis.achievement_quantifier import AchievementQuantifier
from analysis.gap_analyzer import CareerGapAnalyzer
from analysis.interview_prep import InterviewPrep
from services.github_service import GitHubIntegration
from analysis.evidence_system import EvidenceSystem
from analysis.project_story import ProjectStoryGenerator
from analysis.knowledge_graph import KnowledgeGraphRenderer

@pytest.fixture
def mock_resume():
    return {
        "personal": {
            "name": "Sejal Bhagat",
            "email": "bhagatsejal08@gmail.com",
            "phone": "+91 9022644273",
            "location": "Nagpur, India",
            "linkedin": {"display": "linkedin/Sejal-Bhagat", "url": "https://linkedin.com/in/Sejal-Bhagat"},
            "github":   {"display": "github.com/SejalBhagat03", "url": "https://github.com/SejalBhagat03"},
        },
        "summary": "Full stack engineer working on React and Python.",
        "experience": [],
        "projects": [
            {
                "title": "Labour Management App",
                "tools": "React, Node.js, MongoDB",
                "bullets": [
                    "Built a web application for labor logs.",
                    "Implemented database schemas."
                ]
            }
        ],
        "technical_skills": {
            "Programming": "Python, JavaScript",
            "Frontend": "React, HTML, CSS",
            "Backend": "Node.js, MongoDB"
        },
        "achievements": [],
        "education": [
            {
                "degree": "B.E. Computer Science",
                "institution": "Nagpur University",
                "details": "GPA: 8.5/10",
                "period": "2020-2024"
            }
        ],
        "position_of_responsibility": []
    }

class TestCareerTools:
    def test_master_profile_setup(self, mock_resume):
        ensure_setup(mock_resume)
        mp = load_master_profile()
        assert mp != {}
        assert mp["personal"]["name"] == "Sejal Bhagat"
        
        # Test updating and loading version
        save_version("test_ver", mock_resume)
        assert "test_ver" in list_versions()
        ver = load_version("test_ver")
        assert ver["personal"]["email"] == "bhagatsejal08@gmail.com"

    def test_consistency_checker(self, mock_resume):
        res = ConsistencyChecker.analyze(mock_resume)
        assert isinstance(res["score"], int)
        assert len(res["warnings"]) > 0 # should have some suggestions e.g. unquantified project bullets or missing experience
        assert any(w["type"] == "empty_section" for w in res["warnings"])

    def test_achievement_quantifier(self, mock_resume):
        suggestions = AchievementQuantifier.analyze_bullets(mock_resume)
        assert len(suggestions) > 0
        assert any(s["section"] == "Projects" for s in suggestions)
        assert "%" in suggestions[0]["improved"] or "Lighthouse" in suggestions[0]["improved"] or "100+" in suggestions[0]["improved"]

    def test_gap_analyzer(self, mock_resume):
        res = CareerGapAnalyzer.analyze(mock_resume, "Frontend Developer")
        assert res["match_pct"] > 0
        assert "React" in res["matching"]
        assert len(res["missing"]) > 0
        assert len(res["learning_path"]) > 0

    def test_interview_prep(self, mock_resume):
        prep = InterviewPrep.generate_questions(mock_resume)
        assert len(prep["hr"]) > 0
        assert len(prep["technical"]) > 0
        assert len(prep["projects"]) > 0

    def test_github_integration(self):
        analysis = GitHubIntegration.analyze_profile("sejalbhagat03")
        assert analysis["evidence_score"] > 0
        assert "Python" in analysis["languages"] or "JavaScript" in analysis["languages"]
        assert len(analysis["suggested_projects"]) > 0

    def test_evidence_system(self, mock_resume):
        evidence = EvidenceSystem.calculate_evidence(mock_resume, "sejalbhagat03")
        assert len(evidence) > 0
        assert evidence[0]["confidence"] > 0
        assert any(e["skill"] == "React" for e in evidence)

    def test_project_story_generator(self):
        story = ProjectStoryGenerator.generate_story("Test App", "React, Python", "A mock builder description.")
        assert len(story["bullets"]) == 3
        assert "Test App" in story["linkedin"]
        assert "STAR" in story["portfolio"] or "### About 'Test App'" in story["portfolio"]
        assert story["star"]["situation"] != ""

    def test_knowledge_graph(self, mock_resume):
        html = KnowledgeGraphRenderer.render_graph_html(mock_resume)
        assert "<svg" in html
        assert "React" in html
        assert "Labour Management App" in html
