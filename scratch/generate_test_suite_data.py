import os
import json
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from resume_builder.generators.pdf_generator import build_pdf

def generate_mock_resume_data(index, density="medium"):
    experience_bullets = [
        "Led a team of developers to deliver a high-quality SaaS application in python.",
        "Improved website performance and page speed by 40% using image optimization and CDN caching.",
        "Collaborated with UI/UX designers to implement modern interfaces using React."
    ]
    if density == "short":
        experience_bullets = ["Developed Python scripts for web scraping and data cleaning."]
    elif density == "long":
        experience_bullets = [
            "Designed and implemented high-throughput microservices using FastAPI, Redis, and PostgreSQL.",
            "Integrated OAuth2 and JWT authentication, securing endpoints and client credential flows.",
            "Configured CI/CD pipelines in GitHub Actions to run unit tests, build docker containers, and deploy.",
            "Mentored junior engineers on coding standards, clean code principles, and git workflow.",
            "Optimized SQL queries and database indexes, reducing query response times by 65%.",
            "Deployed software applications to AWS EC2 using Docker, Nginx, and systemd monitoring."
        ]
        
    data = {
        "personal": {
            "name": f"TEST CANDIDATE {index}",
            "location": "New York, USA",
            "phone": f"+1 555-010-100{index}",
            "email": f"candidate{index}@example.com",
            "linkedin": {
                "display": f"linkedin.com/in/candidate{index}",
                "url": f"https://linkedin.com/in/candidate{index}"
            },
            "github": {
                "display": f"github.com/candidate{index}",
                "url": f"https://github.com/candidate{index}"
            }
        },
        "summary": f"Highly motivated software developer with experience in python and build pipelines. Candidate number {index}.",
        "experience": [
            {
                "role": "Software Engineer",
                "company": f"Tech Company {index}",
                "location": "Remote",
                "period": "2024 - Present",
                "technologies": "Python, SQL, AWS",
                "bullets": experience_bullets
            }
        ],
        "projects": [
            {
                "title": f"Project Delta {index}",
                "link": f"https://github.com/candidate{index}/project",
                "date": "2023",
                "tools": "Streamlit, PyPDF",
                "bullets": [
                    "Developed a resume building platform using streamlit and ReportLab.",
                    "Implemented layout extraction and parsing engines."
                ]
            }
        ],
        "technical_skills": {
            "Languages": "Python, JavaScript, SQL",
            "Tools": "Git, Docker, AWS"
        },
        "achievements": [
            "Hackathon winner at TechMeet 2025.",
            f"Employee of the Month at Tech Company {index}."
        ],
        "education": [
            {
                "degree": "B.S. in Computer Science",
                "institution": f"University of Technology {index}",
                "details": "GPA: 3.8/4.0",
                "period": "2020 - 2024"
            }
        ],
        "position_of_responsibility": [
            {
                "role": "Team Lead, Open Source Club",
                "period": "2023",
                "bullets": ["Organized weekly developer meetups and coding workshops."]
            }
        ]
    }
    return data

def main():
    corpus_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_corpus"))
    os.makedirs(corpus_dir, exist_ok=True)
    
    # 25 configurations
    # Varying templates, colors, margins, scales, and content densities
    templates = ["sejal_original", "ats", "modern", "creative", "minimal", "two_column"]
    colors_accent = ["#2563EB", "#10B981", "#EF4444", "#8B5CF6", "#475569", "#000000"]
    margins = [12, 16, 20, 24, 28, 32]
    scales = [0.8, 0.9, 1.0, 1.1, 1.2]
    densities = ["short", "medium", "long"]
    
    print(f"Generating 25 diverse resume test cases in {corpus_dir}...")
    
    for i in range(1, 26):
        # Deterministic variation based on index
        template_id = templates[i % len(templates)]
        accent_color = colors_accent[i % len(colors_accent)]
        margin_size = margins[i % len(margins)]
        font_scale = scales[i % len(scales)]
        density = densities[i % len(densities)]
        
        data = generate_mock_resume_data(i, density)
        
        # Save JSON
        json_path = os.path.join(corpus_dir, f"candidate_{i}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            
        # Compile PDF
        pdf_path = os.path.join(corpus_dir, f"candidate_{i}.pdf")
        success, msg = build_pdf(
            data=data,
            template_id=template_id,
            pdf_filename=pdf_path,
            accent_color=accent_color,
            font_scale=font_scale,
            margin_size=margin_size,
            auto_compress=(density != "long"), # Compress medium/short, allow overflow check for long
            allow_multi_page=(density == "long"),
            aggressive_compact=True
        )
        if success:
            print(f"Generated case {i}/25: {template_id}, margin={margin_size}, scale={font_scale}, density={density} -> Success")
        else:
            print(f"Generated case {i}/25: {template_id} -> Failed compilation: {msg}")

if __name__ == "__main__":
    main()
