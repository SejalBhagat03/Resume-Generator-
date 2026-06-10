import re

def calculate_health_score(data):
    """
    Calculates the Layout Fit Score (0-100) and compiles dynamic advice.
    
    Args:
        data (dict): The resume data config.
        
    Returns:
        dict: A report containing layout fitness score, list of suggestions, and health ratings.
    """
    score = 100
    suggestions = []
    health_reports = {}
    
    summary = data.get("summary", "").strip()
    experience = data.get("experience", [])
    projects = data.get("projects", [])
    skills = data.get("technical_skills", {})
    achievements = data.get("achievements", [])
    personal = data.get("personal", {})
    education = data.get("education", [])

    # 0. Critical Missing Sections
    name = personal.get("name", "").strip()
    email = personal.get("email", "").strip()
    phone = personal.get("phone", "").strip()

    if not name:
        score -= 20
        suggestions.append("Your resume has no name! Add your full name in the Contact tab.")
    if not email and not phone:
        score -= 15
        suggestions.append("Add at least an email or phone number so recruiters can contact you.")
    elif not email:
        score -= 5
        suggestions.append("Consider adding an email address — it's the most common way recruiters reach out.")

    if not experience and not projects:
        score -= 20
        suggestions.append("Add at least one experience or project entry to showcase your work.")
    elif not experience:
        score -= 5
        suggestions.append("Consider adding work experience if you have any — even internships count.")

    if not education:
        score -= 10
        suggestions.append("Add your education details — most recruiters expect to see this section.")

    if not summary:
        score -= 5
        suggestions.append("Add a professional summary (40-80 words) to introduce yourself at the top of your resume.")
    
    # 1. Summary Analysis
    summary_words = len(summary.split()) if summary else 0
    health_reports["summary"] = {
        "count": summary_words,
        "range": "40-80 words",
        "status": "green"
    }
    if summary_words > 0:
        if summary_words < 40:
            health_reports["summary"]["status"] = "yellow"
            health_reports["summary"]["message"] = "Summary is slightly shorter than recommended."
            score -= 5
            suggestions.append(f"Consider expanding your summary (currently {summary_words} words) to about 50 words to highlight your core profile.")
        elif summary_words > 80:
            health_reports["summary"]["status"] = "red"
            health_reports["summary"]["message"] = "Summary exceeds recommended length."
            score -= min(15, int((summary_words - 80) * 0.3))
            suggestions.append(f"Consider shortening your professional summary by {summary_words - 80} words to improve layout spacing.")
            
    # 2. Experience Analysis
    exp_bullets_count = 0
    exp_bullets_words = 0
    for job in experience:
        bullets = job.get("bullets", [])
        exp_bullets_count += len(bullets)
        for b in bullets:
            exp_bullets_words += len(b.split())
            
    avg_exp_bullet = (exp_bullets_words / exp_bullets_count) if exp_bullets_count > 0 else 0
    health_reports["experience_bullets"] = {
        "count": int(avg_exp_bullet),
        "range": "15-30 words/bullet",
        "status": "green"
    }
    if avg_exp_bullet > 30:
        health_reports["experience_bullets"]["status"] = "yellow"
        score -= 10
        suggestions.append(f"Your experience bullets are wordy (avg {int(avg_exp_bullet)} words). Aim for 15-30 words to keep bullet points punchy.")
        
    if len(experience) > 4:
        score -= 8
        suggestions.append(f"You have {len(experience)} jobs listed. Consider listing only the top 3-4 most relevant roles to prevent page overflow.")

    # 3. Projects Analysis
    proj_bullets_count = 0
    proj_bullets_words = 0
    for proj in projects:
        bullets = proj.get("bullets", [])
        proj_bullets_count += len(bullets)
        for b in bullets:
            proj_bullets_words += len(b.split())
            
    avg_proj_bullet = (proj_bullets_words / proj_bullets_count) if proj_bullets_count > 0 else 0
    health_reports["project_bullets"] = {
        "count": int(avg_proj_bullet),
        "range": "20-60 words/bullet",
        "status": "green"
    }
    if avg_proj_bullet > 60:
        health_reports["project_bullets"]["status"] = "red"
        score -= 10
        suggestions.append(f"Your project bullets are very long (avg {int(avg_proj_bullet)} words). Trim them down to focus on key contributions.")

    # 4. Skills count
    total_skills = 0
    for cat_name, cat_val in skills.items():
        skills_list = [s.strip() for s in cat_val.split(",") if s.strip()]
        total_skills += len(skills_list)
        
    health_reports["skills"] = {
        "count": total_skills,
        "range": "5-15 skills",
        "status": "green"
    }
    if total_skills > 20:
        health_reports["skills"]["status"] = "yellow"
        score -= 5
        suggestions.append(f"You listed {total_skills} skills. Prioritize the top 15 core skills to avoid cluttering the sidebar.")

    # 5. Achievements
    ach_count = len(achievements)
    health_reports["achievements"] = {
        "count": ach_count,
        "range": "3-5 bullets",
        "status": "green"
    }
    if ach_count > 5:
        health_reports["achievements"]["status"] = "yellow"
        score -= 5
        suggestions.append(f"You listed {ach_count} achievements. Try to select the top 3-5 most high-impact results.")

    # 6. Overall Word count & Density
    text_content = summary + " "
    for job in experience:
        text_content += f" {job.get('role', '')} {job.get('company', '')} " + " ".join(job.get("bullets", []))
    for proj in projects:
        text_content += f" {proj.get('title', '')} " + " ".join(proj.get("bullets", []))
    for ach in achievements:
        text_content += f" {ach} "
        
    words = text_content.split()
    total_words = len(words)
    
    if total_words > 600:
        over = total_words - 600
        score -= min(20, int(over * 0.15))
        suggestions.append(f"Overall length is high ({total_words} words). Consider condensing bullet points to fit a premium single page.")
        
    # Check for metrics
    metrics_count = 0
    for job in experience:
        for bullet in job.get("bullets", []):
            if re.search(r'\b\d+%?\b', bullet):
                metrics_count += 1
    for proj in projects:
        for bullet in proj.get("bullets", []):
            if re.search(r'\b\d+%?\b', bullet):
                metrics_count += 1
                
    if metrics_count < 2:
        score -= 10
        suggestions.append("Quantify your achievements! Try to add metrics (e.g. 'boosted speeds by 30%', 'reduced loading latency').")
        
    # Clamp score
    score = max(0, min(100, score))
    
    return {
        "score": score,
        "suggestions": suggestions,
        "health_reports": health_reports,
        "word_count": total_words
    }
