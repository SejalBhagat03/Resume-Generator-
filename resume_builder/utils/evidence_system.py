import re
from resume_builder.utils.github_integration import GitHubIntegration

class EvidenceSystem:
    @staticmethod
    def calculate_evidence(resume_data: dict, github_username: str = None) -> list:
        """
        Calculate evidence metrics and confidence scores for each skill in the resume.
        """
        skills_section = resume_data.get("technical_skills", {})
        skills_list = []
        
        # 1. Collect user skills
        for cat, val in skills_section.items():
            if val:
                for s in re.split(r"[,;]", val):
                    s_clean = s.strip()
                    if s_clean:
                        skills_list.append((s_clean, s_clean.lower()))
                        
        if not skills_list:
            return []

        # 2. Extract context text from resume projects and experience
        projects = resume_data.get("projects", [])
        experience = resume_data.get("experience", [])
        achievements = resume_data.get("achievements", [])
        
        # 3. Pull GitHub cache if username available
        github_repos = []
        if github_username:
            github_repos = GitHubIntegration.fetch_repos(github_username)

        evidence_reports = []
        for name, name_lower in skills_list:
            score = 0
            sources = []
            
            # Check Resume Project Evidence (+40%)
            found_proj = False
            for p in projects:
                p_text = f"{p.get('title', '')} {p.get('tools', '')} " + " ".join(p.get("bullets", []))
                if re.search(rf"\b{re.escape(name_lower)}\b", p_text.lower()):
                    found_proj = True
                    break
            if found_proj:
                score += 40
                sources.append("✓ Resume Project")
                
            # Check GitHub Repository Evidence (+40%)
            found_github = False
            for r in github_repos:
                r_text = f"{r.get('name', '')} {r.get('language', '') or ''} " + " ".join(r.get("topics", []))
                if re.search(rf"\b{re.escape(name_lower)}\b", r_text.lower()):
                    found_github = True
                    break
            if found_github:
                score += 40
                sources.append("✓ GitHub Repository")
                
            # Check Work Experience or Certification (+20%)
            found_exp_cert = False
            for e in experience:
                e_text = f"{e.get('role', '')} {e.get('company', '')} {e.get('technologies', '')} " + " ".join(e.get("bullets", []))
                if re.search(rf"\b{re.escape(name_lower)}\b", e_text.lower()):
                    found_exp_cert = True
                    break
            if not found_exp_cert:
                for a in achievements:
                    if re.search(rf"\b{re.escape(name_lower)}\b", a.lower()):
                        found_exp_cert = True
                        break
                        
            if found_exp_cert:
                score += 20
                sources.append("✓ Experience / Achievement")
                
            # Final scoring bound
            score = min(100, score)
            
            evidence_reports.append({
                "skill": name,
                "confidence": score,
                "sources": sources,
                "unsupported": score < 40
            })
            
        # Sort skills by confidence score descending
        return sorted(evidence_reports, key=lambda x: x["confidence"], reverse=True)
