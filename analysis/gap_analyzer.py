import re

class CareerGapAnalyzer:
    ROLE_REQUIREMENTS = {
        "Frontend Developer": {
            "skills": ["html", "css", "javascript", "react", "redux", "typescript", "git", "jest", "responsive design", "webpack"],
            "priorities": ["javascript", "react", "typescript", "redux", "css", "jest", "responsive design", "git", "webpack", "html"]
        },
        "Backend Developer": {
            "skills": ["python", "node.js", "express", "sql", "mongodb", "postgresql", "docker", "apis", "aws", "git"],
            "priorities": ["node.js", "sql", "python", "mongodb", "apis", "docker", "postgresql", "express", "aws", "git"]
        },
        "Full Stack Developer": {
            "skills": ["html", "css", "javascript", "react", "node.js", "express", "mongodb", "sql", "git", "apis", "docker", "typescript"],
            "priorities": ["javascript", "react", "node.js", "mongodb", "sql", "typescript", "apis", "css", "git", "docker", "express", "html"]
        },
        "Data Analyst": {
            "skills": ["python", "sql", "excel", "tableau", "pandas", "numpy", "power bi", "statistics", "data visualization", "r"],
            "priorities": ["sql", "python", "pandas", "tableau", "excel", "numpy", "statistics", "data visualization", "power bi", "r"]
        },
        "Python Developer": {
            "skills": ["python", "django", "flask", "sql", "git", "apis", "pandas", "docker", "numpy", "algorithms"],
            "priorities": ["python", "django", "sql", "git", "apis", "flask", "docker", "algorithms", "pandas", "numpy"]
        }
    }

    LEARNING_PATH_RECOMMENDATIONS = {
        "typescript": "Learn TypeScript Basics & Types on TypeScriptLang.org. Build a small project replacing Javascript with strongly-typed interfaces.",
        "redux": "Check out Redux Toolkit documentation (redux-toolkit.js.org). Learn Slice creation, store setup, and asynchronous thunks.",
        "jest": "Learn unit testing concepts. Write Jest tests for pure JS functions and study mock functions/expectations.",
        "node.js": "Build asynchronous servers using Node.js filesystem modules and routing. Complete Node.js courses on freeCodeCamp.",
        "express": "Learn middlewares, routing, and REST controller architectures using Express.js.",
        "sql": "Study PostgreSQL/MySQL schemas, JOINs, indexing, and normal forms. Practice on LeetCode SQL challenges.",
        "mongodb": "Learn NoSQL design, aggregation pipelines, and document schemas. Take MongoDB University courses.",
        "docker": "Learn containerization basics. Write Dockerfiles for your node/python apps and test docker-compose.",
        "aws": "Study AWS EC2, S3 bucket storage, and IAM roles. Learn to deploy static websites and server setups.",
        "tableau": "Learn to connect datasets and build interactive metrics dashboards. Explore Tableau Public dashboards.",
        "power bi": "Learn to write DAX expressions and structure dimensional schemas using Power BI Desktop.",
        "pandas": "Learn data structures like Series/DataFrames. Practice filtering, grouping, and aggregations.",
        "django": "Learn Django MVC architecture, models, migrations, views, and template configurations.",
        "flask": "Learn to set up lightweight server endpoints, request handling, and blueprint routing in Python."
    }

    @staticmethod
    def analyze(resume_data: dict, target_role: str) -> dict:
        """
        Analyze current resume skills against the selected target role.
        Returns score, match percentage, missing skills, and prioritized learning recommendations.
        """
        if target_role not in CareerGapAnalyzer.ROLE_REQUIREMENTS:
            return {"score": 0, "matching": [], "missing": [], "learning_path": []}

        # 1. Parse active skills
        skills_section = resume_data.get("technical_skills", {})
        user_skills = set()
        for cat, val in skills_section.items():
            if val:
                for s in re.split(r"[,;]", val):
                    s_clean = s.strip().lower()
                    if s_clean:
                        user_skills.add(s_clean)

        reqs = CareerGapAnalyzer.ROLE_REQUIREMENTS[target_role]
        required_skills = reqs["skills"]
        priorities = reqs["priorities"]

        matching = []
        missing = []

        # Compare
        for skill in required_skills:
            # check direct or partial regex boundary matching
            found = False
            for us in user_skills:
                if skill == us or re.search(rf"\b{re.escape(skill)}\b", us) or re.search(rf"\b{re.escape(us)}\b", skill):
                    found = True
                    break
            if found:
                matching.append(skill)
            else:
                missing.append(skill)

        # Sort missing skills by priority order defined in the role
        missing_sorted = sorted(missing, key=lambda x: priorities.index(x) if x in priorities else 99)

        # Generate learning path recommendations
        learning_path = []
        for rank, skill in enumerate(missing_sorted, 1):
            rec = CareerGapAnalyzer.LEARNING_PATH_RECOMMENDATIONS.get(
                skill, 
                f"Study '{skill.title()}' online documentation, take introductory courses, and build a hands-on project."
            )
            learning_path.append({
                "priority": rank,
                "skill": skill.title(),
                "action": rec
            })

        # Calculate percentage match score
        total = len(required_skills)
        match_count = len(matching)
        match_pct = int((match_count / total) * 100) if total > 0 else 0

        return {
            "role": target_role,
            "match_pct": match_pct,
            "matching": [s.title() for s in matching],
            "missing": [s.title() for s in missing_sorted],
            "learning_path": learning_path
        }
