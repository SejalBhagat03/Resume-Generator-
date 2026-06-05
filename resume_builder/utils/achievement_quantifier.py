import re

class AchievementQuantifier:
    @staticmethod
    def contains_number(text: str) -> bool:
        """Check if bullet text already contains a number (indicating it is quantified)."""
        return bool(re.search(r"\b\d+%?\b", text))

    @staticmethod
    def analyze_bullets(resume_data: dict) -> list:
        """
        Scan all bullet points from projects and experience.
        If a bullet is not quantified, match it against common patterns and suggest improvements.
        """
        suggestions = []
        
        # Helper to process bullets
        def process_section_bullets(items, section_name):
            for item_idx, item in enumerate(items):
                title = item.get("title", item.get("role", "Entry"))
                bullets = item.get("bullets", [])
                for bullet_idx, bullet in enumerate(bullets):
                    if not AchievementQuantifier.contains_number(bullet):
                        # Find patterns to suggest improvements
                        suggested = AchievementQuantifier.generate_suggestion(bullet)
                        if suggested:
                            suggestions.append({
                                "section": section_name,
                                "item_index": item_idx,
                                "bullet_index": bullet_idx,
                                "item_title": title,
                                "original": bullet,
                                "improved": suggested["improved"],
                                "reason": suggested["reason"]
                            })

        process_section_bullets(resume_data.get("projects", []), "Projects")
        process_section_bullets(resume_data.get("experience", []), "Experience")
        return suggestions

    @staticmethod
    def generate_suggestion(bullet: str) -> dict:
        """Analyze bullet text and generate a quantified rephrasing."""
        b_lower = bullet.lower()
        
        # Rule 1: Web application building
        if any(w in b_lower for w in ["web application", "website", "platform", "app"]):
            return {
                "improved": bullet.rstrip(".") + " serving 100+ active users and improving response times by 30%.",
                "reason": "Specify user load, traffic metrics, or response time speed improvements to demonstrate performance tuning."
            }
            
        # Rule 2: Databases, backend systems, APIs
        if any(w in b_lower for w in ["database", "schema", "api", "backend", "server"]):
            return {
                "improved": bullet.rstrip(".") + " optimizing database queries to reduce query latency by 15% for over 10k+ records.",
                "reason": "Quantify backend efficiency by detailing data scale (records) or query latency speedup."
            }

        # Rule 3: Manual operations, pipelines, scraping
        if any(w in b_lower for w in ["scraping", "scraper", "automation", "script", "pipeline"]):
            return {
                "improved": bullet.rstrip(".") + " reducing manual operational task times by 40% and increasing data collection speeds.",
                "reason": "Demonstrate efficiency gains. Operational tools are best quantified by percentage of manual workload reduced."
            }

        # Rule 4: HTML, CSS, frontend design, responsive
        if any(w in b_lower for w in ["ui", "css", "frontend", "responsive", "react", "interface"]):
            return {
                "improved": bullet.rstrip(".") + " achieving a 95+ performance score on Lighthouse and ensuring 100% responsiveness on mobile.",
                "reason": "Use measurable design standard metrics like Lighthouse scores or cross-device compatibility ratios."
            }

        # Rule 5: Generic developer bullets
        return {
            "improved": bullet.rstrip(".") + " resulting in a 25% increase in team development velocity and a 15% decrease in bugs.",
            "reason": "Add business value metrics, detailing how your work speeded up development or reduced software defects."
        }
