import os
import json
import copy

# Load main resume data as base
base_path = "resume.json"
with open(base_path, "r", encoding="utf-8") as f:
    base_data = json.load(f)

versions_dir = "resume_versions"
os.makedirs(versions_dir, exist_ok=True)

# 1. SOFTWARE TECHNOLOGY (WEB TECHNOLOGIES)
st_data = copy.deepcopy(base_data)
st_data["summary"] = "Final-year Computer Science Engineering student with hands-on software developer internship experience. Skilled in modern web architectures, scalable API development, and software design patterns. Proven record of building secure, database-driven web applications and solving complex algorithmic challenges."
st_data["technical_skills"] = {
    "Programming": "C++, Python, JavaScript, TypeScript, C",
    "Web Technologies": "HTML5, CSS3, React.js, Tailwind CSS, Bootstrap, Node.js, Express.js, REST APIs",
    "Databases": "PostgreSQL, MongoDB, MySQL",
    "Tools & Platform": "Git, GitHub, Postman, VS Code, Vite, Docker, Cloudflare, Netlify",
    "Core CS": "Data Structures & Algorithms, OOP, DBMS, Operating Systems, Computer Networks"
}
# Order projects to emphasize Web Technologies: Labor -> RateHub -> Blockchain
st_data["projects"] = [
    base_data["projects"][1], # Labor Management System
    base_data["projects"][2], # Store Review Platform (RateHub)
    base_data["projects"][0]  # Blockchain-Based Digital License
]
st_data["metadata"] = {"locked": False}

# 2. FULL STACK DEVELOPER
fs_data = copy.deepcopy(base_data)
fs_data["summary"] = "Final-year Computer Science Engineering student with professional experience as a Software Developer Intern. Specialized in end-to-end web engineering, from crafting responsive React user interfaces to developing robust backend REST APIs and managing database architectures (SQL & NoSQL)."
fs_data["technical_skills"] = {
    "Frontend": "HTML5, CSS3, React.js, Tailwind CSS, Bootstrap, JavaScript (ES6+), TypeScript",
    "Backend": "Node.js, Express.js, REST APIs, JWT Authentication, Firebase",
    "Databases": "PostgreSQL, MongoDB, MySQL",
    "Tools & DevOps": "Git, GitHub, Postman, Docker, Vite, VS Code, npm/yarn",
    "Languages": "JavaScript, TypeScript, Python, C++, C",
    "Core CS": "Data Structures & Algorithms, OOP, DBMS, Operating Systems, Computer Networks"
}
# Projects order: Labor -> RateHub -> Blockchain
fs_data["projects"] = [
    base_data["projects"][1],
    base_data["projects"][2],
    base_data["projects"][0]
]
fs_data["metadata"] = {"locked": False}

# 3. WEB DEVELOPER
wd_data = copy.deepcopy(base_data)
wd_data["summary"] = "Motivated Computer Science Engineering student and Web Developer with internship experience in building responsive web layouts, highly interactive user experiences, and client-side logic. Skilled in HTML, CSS, JavaScript, React, and modern CSS frameworks like Tailwind and Bootstrap."
wd_data["technical_skills"] = {
    "Frontend Development": "React.js, JavaScript, TypeScript, HTML5, CSS3, Tailwind CSS, Bootstrap",
    "APIs & Backend": "Node.js, Express.js, RESTful APIs, JWT Authentication, Firebase",
    "Databases": "MongoDB, PostgreSQL, MySQL",
    "Tools & Hosting": "Git, GitHub, Netlify, Cloudflare, VS Code, Vite, Postman",
    "Languages": "JavaScript, TypeScript, Python, C++",
    "Core CS": "Data Structures & Algorithms, OOP, DBMS"
}
# Projects order: RateHub -> Labor -> Blockchain
wd_data["projects"] = [
    base_data["projects"][2],
    base_data["projects"][1],
    base_data["projects"][0]
]
wd_data["metadata"] = {"locked": False}

# 4. ARTIFICIAL INTELLIGENCE/MACHINE LEARNING
ai_data = copy.deepcopy(base_data)
ai_data["summary"] = "Final-year Computer Science Engineering student with an interest in Machine Learning, Optical Character Recognition (OCR), and AI-assisted data extraction. Experienced in integrating intelligence and automation workflows into software platforms."
ai_data["technical_skills"] = {
    "AI/ML & Data Science": "Python, OCR (Tesseract), AI-assisted Data Extraction, NumPy, Pandas, Scikit-Learn, Machine Learning Fundamentals",
    "Languages": "Python, C++, JavaScript, TypeScript",
    "Web Integration": "Node.js, Express.js, REST APIs, FastAPI, Postman",
    "Databases": "MongoDB, PostgreSQL, MySQL",
    "Tools & Platform": "Git, GitHub, VS Code, Docker, Jupyter Notebook, Vite",
    "Core CS": "Data Structures & Algorithms, OOP, DBMS, Operating Systems"
}
# Projects order: Labor (OCR/AI details) -> Blockchain -> RateHub
# Let's adjust Labor Management System tools / details to highlight AI/ML OCR
lms = copy.deepcopy(base_data["projects"][1])
lms["tools"] = "Python, OCR (Tesseract), React, Node.js, MongoDB, REST APIs"
ai_data["projects"] = [
    lms,
    base_data["projects"][0],
    base_data["projects"][2]
]
ai_data["metadata"] = {"locked": False}

# 5. FRONTEND DEVELOPER
fe_data = copy.deepcopy(base_data)
fe_data["summary"] = "Specialized Frontend Developer and Software Developer Intern. Experienced in building responsive visual interfaces, reusable React components, and user-centric layouts. Strong focus on UI/UX excellence, performance optimization, and client-side logic."
fe_data["technical_skills"] = {
    "Core Frontend": "React.js, JavaScript (ES6+), TypeScript, HTML5, CSS3",
    "Styling & UI": "Tailwind CSS, Bootstrap, Responsive Web Design, CSS layouts",
    "State & Tooling": "Context API, Vite, npm/yarn, Chrome DevTools",
    "APIs & Integration": "REST APIs, JSON, Postman, Firebase",
    "Developer Tools": "Git, GitHub, VS Code, Docker",
    "Languages": "JavaScript, TypeScript, Python, C++",
    "Core CS": "Data Structures & Algorithms, OOP"
}
# Projects order: Labor -> RateHub -> Blockchain
fe_data["projects"] = [
    base_data["projects"][1],
    base_data["projects"][2],
    base_data["projects"][0]
]
fe_data["metadata"] = {"locked": False}

# 6. BACKEND DEVELOPER
be_data = copy.deepcopy(base_data)
be_data["summary"] = "Focused Backend Developer and Software Developer Intern. Experienced in designing robust server-side logic, secure RESTful APIs, and SQL/NoSQL database architectures. Skilled in authentication models (JWT), authorization controls, and system optimization."
be_data["technical_skills"] = {
    "Backend Engineering": "Node.js, Express.js, RESTful APIs, JWT Authentication, FastAPI",
    "Databases": "PostgreSQL, MongoDB, MySQL, Database Normalization & Indexing",
    "Security & Systems": "Role-based Access Control (RBAC), Data Sanitization, Input Validation",
    "Tools & DevOps": "Git, GitHub, Postman, Docker, Linux Command Line",
    "Languages": "Python, JavaScript, TypeScript, C++, C",
    "Core CS": "Data Structures & Algorithms, DBMS, Operating Systems, Computer Networks"
}
# Projects order: RateHub (highlight JWT/Auth) -> Labor (REST APIs/Validation) -> Blockchain (smart contracts API)
ratehub = copy.deepcopy(base_data["projects"][2])
ratehub["tools"] = "Node.js, Express.js, PostgreSQL, REST APIs, JWT Authentication"
labor = copy.deepcopy(base_data["projects"][1])
labor["tools"] = "Node.js, MongoDB, REST APIs, JWT, Backend Validation"
be_data["projects"] = [
    ratehub,
    labor,
    base_data["projects"][0]
]
be_data["metadata"] = {"locked": False}

# Write files to resume_versions/
files_to_write = {
    "software_technology_web_technologies.json": st_data,
    "full_stack_developer.json": fs_data,
    "web_developer.json": wd_data,
    "artificial_intelligence_machine_learning.json": ai_data,
    "frontend_developer.json": fe_data,
    "backend_developer.json": be_data
}

for filename, content in files_to_write.items():
    dest_path = os.path.join(versions_dir, filename)
    with open(dest_path, "w", encoding="utf-8") as f:
        json.dump(content, f, indent=2)
    print(f"Created/Updated: {dest_path}")

print("Successfully created all 6 specialized resumes.")
