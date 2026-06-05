"""
Basic tests for Resume Builder Pro core functions.
Run with: python -m pytest tests/ -v
"""
import os
import sys
import json
import copy
import pytest

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from resume_builder.generators.pdf_generator import build_pdf
from resume_builder.utils.health_scorer import calculate_health_score
from resume_builder.templates import TEMPLATES, register_templates, get_template_class


# ─────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────
@pytest.fixture
def sample_resume():
    return {
        "personal": {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+1 555-1234",
            "location": "New York, USA",
            "linkedin": {"display": "linkedin/test", "url": "https://linkedin.com/in/test"},
            "github": {"display": "github.com/test", "url": "https://github.com/test"},
        },
        "summary": "Experienced software engineer with expertise in Python and web development.",
        "experience": [
            {
                "role": "Software Engineer",
                "company": "Acme Corp",
                "location": "Remote",
                "period": "2023–Present",
                "technologies": "Python, Django, PostgreSQL",
                "bullets": [
                    "Built REST APIs serving 10,000+ daily requests.",
                    "Reduced deployment time by 50% with CI/CD pipeline.",
                ],
            }
        ],
        "projects": [
            {
                "title": "Portfolio Site",
                "link": "https://example.com",
                "date": "2023",
                "tools": "React, Next.js",
                "bullets": ["Designed and deployed a personal portfolio website."],
            }
        ],
        "technical_skills": {
            "Languages": "Python, JavaScript, SQL",
            "Frameworks": "Django, React, Node.js",
        },
        "achievements": [
            "Won first place in university hackathon.",
            "Published 2 open-source libraries with 500+ GitHub stars.",
        ],
        "education": [
            {
                "degree": "B.S. Computer Science",
                "institution": "State University",
                "details": "GPA: 3.8/4.0",
                "period": "2019–2023",
            }
        ],
        "position_of_responsibility": [],
    }


@pytest.fixture
def empty_resume():
    return {
        "personal": {
            "name": "",
            "email": "",
            "phone": "",
            "location": "",
            "linkedin": {"display": "", "url": ""},
            "github": {"display": "", "url": ""},
        },
        "summary": "",
        "experience": [],
        "projects": [],
        "technical_skills": {},
        "achievements": [],
        "education": [],
        "position_of_responsibility": [],
    }


@pytest.fixture
def pdf_output_path(tmp_path):
    return str(tmp_path / "test_output.pdf")


# ─────────────────────────────────────────────────────
# Tests: PDF Generation
# ─────────────────────────────────────────────────────
class TestBuildPdf:
    def test_build_pdf_success(self, sample_resume, pdf_output_path):
        """PDF should compile successfully with valid data."""
        ok, msg = build_pdf(
            data=sample_resume,
            template_id="sejal_original",
            pdf_filename=pdf_output_path,
        )
        assert ok is True
        assert os.path.exists(pdf_output_path)
        assert os.path.getsize(pdf_output_path) > 0

    def test_build_pdf_with_empty_data(self, empty_resume, pdf_output_path):
        """PDF should still compile with empty resume data (no crash)."""
        ok, msg = build_pdf(
            data=empty_resume,
            template_id="sejal_original",
            pdf_filename=pdf_output_path,
        )
        assert ok is True
        assert os.path.exists(pdf_output_path)

    def test_build_pdf_custom_settings(self, sample_resume, pdf_output_path):
        """PDF should compile with custom margin, font scale, and accent."""
        ok, msg = build_pdf(
            data=sample_resume,
            template_id="sejal_original",
            pdf_filename=pdf_output_path,
            accent_color="#E11D48",
            font_scale=0.85,
            margin_size=12,
        )
        assert ok is True
        assert os.path.exists(pdf_output_path)

    def test_build_pdf_invalid_template_falls_back(self, sample_resume, pdf_output_path):
        """Invalid template ID should fall back to sejal_original."""
        ok, msg = build_pdf(
            data=sample_resume,
            template_id="nonexistent_template_xyz",
            pdf_filename=pdf_output_path,
        )
        assert ok is True


# ─────────────────────────────────────────────────────
# Tests: Health Scorer
# ─────────────────────────────────────────────────────
class TestHealthScorer:
    def test_good_resume_scores_high(self, sample_resume):
        """A well-structured resume should score >= 70."""
        result = calculate_health_score(sample_resume)
        assert result["score"] >= 70
        assert isinstance(result["suggestions"], list)

    def test_empty_resume_returns_valid_result(self, empty_resume):
        """Empty resume should not crash, should return valid dict."""
        result = calculate_health_score(empty_resume)
        assert "score" in result
        assert "suggestions" in result
        assert 0 <= result["score"] <= 100

    def test_wordy_summary_penalized(self, sample_resume):
        """A summary over 80 words should be penalized."""
        sample_resume["summary"] = " ".join(["word"] * 120)
        result = calculate_health_score(sample_resume)
        assert result["score"] < 100
        assert any("summary" in s.lower() for s in result["suggestions"])

    def test_too_many_jobs_penalized(self, sample_resume):
        """More than 4 experience entries should be penalized."""
        sample_resume["experience"] = [
            {"role": f"Role {i}", "company": f"Co {i}", "bullets": ["Did stuff."]}
            for i in range(6)
        ]
        result = calculate_health_score(sample_resume)
        assert any("jobs" in s.lower() or "roles" in s.lower() for s in result["suggestions"])

    def test_no_metrics_penalized(self, sample_resume):
        """Bullets without numbers should trigger a metrics suggestion."""
        for exp in sample_resume["experience"]:
            exp["bullets"] = ["Worked on backend systems.", "Improved code quality."]
        for proj in sample_resume["projects"]:
            proj["bullets"] = ["Built a website using modern tools."]
        result = calculate_health_score(sample_resume)
        assert any("quantify" in s.lower() or "metric" in s.lower() for s in result["suggestions"])


# ─────────────────────────────────────────────────────
# Tests: Template Registry
# ─────────────────────────────────────────────────────
class TestTemplateRegistry:
    def test_templates_registered(self):
        """At least one template should be registered."""
        register_templates()
        assert len(TEMPLATES) > 0

    def test_sejal_original_exists(self):
        """The default template should always exist."""
        register_templates()
        assert "sejal_original" in TEMPLATES

    def test_get_template_class_returns_class(self):
        """get_template_class should return a valid class."""
        cls = get_template_class("sejal_original")
        assert cls is not None
        assert hasattr(cls, "generate")

    def test_invalid_template_falls_back(self):
        """Invalid template ID should fall back to sejal_original."""
        cls = get_template_class("totally_fake_id")
        assert cls is not None


# ─────────────────────────────────────────────────────
# Tests: Input Sanitization
# ─────────────────────────────────────────────────────
class TestSanitization:
    def test_strips_script_tags(self):
        from resume_builder.app import sanitize_html
        result = sanitize_html('<script>alert("xss")</script>Hello')
        assert "<script>" not in result
        assert "Hello" in result

    def test_keeps_safe_bold_tag(self):
        from resume_builder.app import sanitize_html
        result = sanitize_html("<b>Bold text</b>")
        assert "<b>" in result

    def test_strips_img_tag(self):
        from resume_builder.app import sanitize_html
        result = sanitize_html('<img src="x" onerror="alert(1)">Text')
        assert "<img" not in result
        assert "Text" in result

    def test_handles_empty_string(self):
        from resume_builder.app import sanitize_html
        assert sanitize_html("") == ""

    def test_handles_none(self):
        from resume_builder.app import sanitize_html
        assert sanitize_html(None) is None
