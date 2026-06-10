import re

class InterviewPrep:
    HR_QUESTIONS = [
        {
            "question": "Tell me about yourself and walk me through your resume.",
            "reason": "Assess communication skills, logical structure of career trajectory, and highlight reel.",
            "expected_topics": ["Overview of education & experience", "Key project highlights", "Career aspirations matching this role"]
        },
        {
            "question": "Describe a difficult technical problem you faced and how you solved it.",
            "reason": "Evaluate problem-solving capabilities, technical depth, and perseverance under pressure.",
            "expected_topics": ["Context/Problem definition", "Actions taken (debugging, tracing, research)", "Result and quantitative outcome"]
        }
    ]

    TECH_QUESTIONS_DATABASE = {
        "react": {
            "question": "What is the virtual DOM in React, and how does reconciliation work?",
            "reason": "Check core understanding of React rendering optimization mechanics.",
            "expected_topics": ["Diffing algorithm", "Key props usage", "Fibers/State batch updates"]
        },
        "python": {
            "question": "How are lists and tuples different in Python? Explain memory allocations.",
            "reason": "Test fundamental understanding of language structures and performance optimizations.",
            "expected_topics": ["Mutability vs Immutability", "Static vs Dynamic resizing", "Tuple caching speeds"]
        },
        "javascript": {
            "question": "What is closure in JavaScript and where is it commonly used?",
            "reason": "Test intermediate scope management concepts and callbacks.",
            "expected_topics": ["Lexical scoping", "Encapsulation / Private variables", "Event handlers & callbacks"]
        },
        "mongodb": {
            "question": "When would you prefer MongoDB over a traditional SQL database?",
            "reason": "Check architectural understanding of system scaling and schema design tradeoffs.",
            "expected_topics": ["Dynamic schemas/JSON documents", "Horizontal scaling/sharding", "Lack of complex multi-table joins"]
        },
        "sql": {
            "question": "What is database normalization, and when is it appropriate to denormalize?",
            "reason": "Assess data modeling skills and transaction design capability.",
            "expected_topics": ["1NF, 2NF, 3NF structures", "Reducing data redundancy", "Read performance scaling via denormalization"]
        },
        "node.js": {
            "question": "Explain the Node.js event loop and how it handles asynchronous operations.",
            "reason": "Verify knowledge of Node's non-blocking I/O runtime model.",
            "expected_topics": ["Single-threaded callback execution", "Libuv handling threadpools", "Phases (timers, poll, check)"]
        }
    }

    @staticmethod
    def generate_questions(resume_data: dict) -> dict:
        """
        Scan skills and projects to generate targeted questions across categories.
        """
        # 1. HR Questions
        hr = list(InterviewPrep.HR_QUESTIONS)

        # 2. Technical Questions from listed skills
        tech = []
        skills_section = resume_data.get("technical_skills", {})
        user_skills = set()
        for cat, val in skills_section.items():
            if val:
                for s in re.split(r"[,;]", val):
                    s_clean = s.strip().lower()
                    if s_clean:
                        user_skills.add(s_clean)

        for skill, data in InterviewPrep.TECH_QUESTIONS_DATABASE.items():
            # Match user skills partially
            for us in user_skills:
                if skill in us or us in skill:
                    tech.append({
                        "skill": skill.title(),
                        "question": data["question"],
                        "reason": data["reason"],
                        "expected_topics": data["expected_topics"]
                    })
                    break # add once per matching database entry

        # Fallback tech question if user has no matching database skills
        if not tech:
            tech.append({
                "skill": "Software Engineering",
                "question": "Explain how you ensure code quality and write clean, maintainable code.",
                "reason": "Assess best practices knowledge, testing, and documentation standards.",
                "expected_topics": ["Code reviews & Git workflow", "Unit testing & coverage", "Clean architecture / SOLID principles"]
            })

        # 3. Project Questions
        project_qs = []
        projects = resume_data.get("projects", [])
        for p in projects:
            title = p.get("title", "Project")
            tools = p.get("tools", "")
            
            # Question 1: Technology selection
            project_qs.append({
                "project": title,
                "question": f"Why did you choose {tools or 'your tech stack'} for the '{title}' project?",
                "reason": "Evaluate architecture design decision-making logic.",
                "expected_topics": ["Specific advantages of technologies used", "Alternative tools considered and rejected", "Ease of integration"]
            })
            
            # Question 2: Implementation / Architecture challenge
            project_qs.append({
                "project": title,
                "question": f"Walk me through the system architecture of '{title}'. How did you implement authentication or data flows?",
                "reason": "Assess hands-on execution and technical ownership of the code.",
                "expected_topics": ["Component relationship hierarchy", "Database structure / API models", "Data validation & security checks"]
            })

        # Fallback if no projects listed
        if not project_qs:
            project_qs.append({
                "project": "General",
                "question": "If you were to start a new project today, what architecture patterns and tech stack would you choose?",
                "reason": "Check forward-looking engineering knowledge.",
                "expected_topics": ["Client-Server structures", "Framework evaluation criteria", "Hosting & cloud deployment considerations"]
            })

        return {
            "hr": hr,
            "technical": tech,
            "projects": project_qs
        }
