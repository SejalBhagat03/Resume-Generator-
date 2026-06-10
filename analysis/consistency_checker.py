import re

class ConsistencyChecker:
    @staticmethod
    def analyze(resume_data: dict) -> dict:
        warnings = []
        
        # 1. Extract skills
        skills_section = resume_data.get("technical_skills", {})
        skills_set = set()
        for cat, val in skills_section.items():
            if val:
                # split by comma or semicolon
                for s in re.split(r"[,;]", val):
                    s_clean = s.strip().lower()
                    if s_clean:
                        skills_set.add((s.strip(), s_clean))
        
        # 2. Extract content text for keyword demonstration search
        projects = resume_data.get("projects", [])
        experience = resume_data.get("experience", [])
        summary = resume_data.get("summary", "")
        
        project_texts = []
        for p in projects:
            proj_str = f"{p.get('title', '')} {p.get('tools', '')} " + " ".join(p.get("bullets", []))
            project_texts.append(proj_str.lower())
            
        exp_texts = []
        for e in experience:
            exp_str = f"{e.get('role', '')} {e.get('company', '')} {e.get('technologies', '')} " + " ".join(e.get("bullets", []))
            exp_texts.append(exp_str.lower())
            
        all_text = " ".join(project_texts + exp_texts + [summary.lower()])
        
        # 3. Detect skills listed but never used
        missing_demonstrations = []
        for original_name, skill_lower in skills_set:
            # simple keyword match boundary
            pattern = rf"\b{re.escape(skill_lower)}\b"
            if not re.search(pattern, all_text):
                missing_demonstrations.append(original_name)
                warnings.append({
                    "type": "skill_not_demonstrated",
                    "severity": "medium",
                    "message": f"Skill '{original_name}' is listed but never demonstrated in your projects, experience, or summary.",
                    "suggestion": f"Add a bullet point in your projects or work experience demonstrating how you used {original_name}."
                })

        # 4. Empty Sections
        empty_sections = []
        for section_name in ["experience", "projects", "education"]:
            if not resume_data.get(section_name):
                empty_sections.append(section_name.title())
                warnings.append({
                    "type": "empty_section",
                    "severity": "high",
                    "message": f"The '{section_name.title()}' section is completely empty.",
                    "suggestion": f"Add at least one entry to your '{section_name.title()}' section to make your resume complete."
                })
                
        # 5. Weak Project Descriptions (short bullets or lack of action verbs)
        weak_bullets = 0
        action_verbs = {"build", "built", "develop", "developed", "create", "created", "design", "designed", 
                        "implement", "implemented", "lead", "led", "manage", "managed", "optimize", "optimized",
                        "write", "wrote", "deploy", "deployed", "increase", "increased", "reduce", "reduced"}
        
        for p in projects:
            title = p.get("title", "Unnamed Project")
            bullets = p.get("bullets", [])
            if not bullets:
                warnings.append({
                    "type": "weak_project",
                    "severity": "high",
                    "message": f"Project '{title}' has no descriptions or bullet points.",
                    "suggestion": f"Add 2-3 descriptive bullet points to project '{title}' showcasing features and tech stack."
                })
            else:
                for b in bullets:
                    words = b.strip().lower().split()
                    if len(words) < 7:
                        weak_bullets += 1
                        warnings.append({
                            "type": "short_bullet",
                            "severity": "low",
                            "message": f"Short bullet point in project '{title}': \"{b}\"",
                            "suggestion": "Expand this bullet point to explain the 'what', 'how', and the result/impact."
                        })
                    elif words and words[0] not in action_verbs:
                        warnings.append({
                            "type": "missing_action_verb",
                            "severity": "medium",
                            "message": f"Description bullet in '{title}' does not start with an action verb: \"{b}\"",
                            "suggestion": f"Start the bullet point with a strong action verb (e.g. 'Developed', 'Optimized', 'Designed')."
                        })
                        
        # 6. Duplicate Content
        seen_bullets = {}
        for p in projects:
            for b in p.get("bullets", []):
                b_clean = b.strip().lower()
                if b_clean:
                    if b_clean in seen_bullets:
                        warnings.append({
                            "type": "duplicate_content",
                            "severity": "medium",
                            "message": f"Duplicate bullet point found: \"{b}\"",
                            "suggestion": "Rephrase this bullet point so each description is unique."
                        })
                    seen_bullets[b_clean] = True

        for e in experience:
            for b in e.get("bullets", []):
                b_clean = b.strip().lower()
                if b_clean:
                    if b_clean in seen_bullets:
                        warnings.append({
                            "type": "duplicate_content",
                            "severity": "medium",
                            "message": f"Duplicate bullet point found: \"{b}\"",
                            "suggestion": "Rephrase this bullet point to highlight unique contributions."
                        })
                    seen_bullets[b_clean] = True

        # Calculate a consistency score (0 - 100)
        # Start at 100, deduct points for warnings depending on severity
        score = 100
        for w in warnings:
            if w["severity"] == "high":
                score -= 15
            elif w["severity"] == "medium":
                score -= 8
            else:
                score -= 3
        score = max(0, score)
        
        return {
            "score": score,
            "warnings": warnings,
            "missing_demonstrations": missing_demonstrations
        }
