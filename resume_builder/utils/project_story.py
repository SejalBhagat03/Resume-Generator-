class ProjectStoryGenerator:
    @staticmethod
    def generate_story(name: str, tech_stack: str, description: str) -> dict:
        """
        Synthesize professional copy based on inputs using robust templates and rules.
        """
        # Clean inputs
        name = name.strip() or "My Project"
        techs = [t.strip() for t in tech_stack.split(",") if t.strip()]
        tech_str = ", ".join(techs) or "Software Engineering patterns"
        desc = description.strip() or "A software application built to solve developer needs."

        # 1. Generate Resume Bullets
        bullets = [
            f"Designed and architected '{name}' using {tech_str} to deliver a modular, responsive user experience.",
            f"Implemented secure API endpoints and optimized database models based on '{desc.rstrip('.')}' specs.",
            f"Configured deployment pipelines and refined rendering operations to reduce response latency by 25%."
        ]

        # 2. LinkedIn Description
        linkedin = (
            f"🚀 Excited to share my latest project: {name}! \n\n"
            f"I built this platform using {tech_str} to solve a key challenge: {desc.rstrip('.')}.\n\n"
            f"Key features include high-performance integrations, clean database design, and a fully responsive interface. "
            f"Check it out and let me know your thoughts!"
        )

        # 3. Portfolio Description
        portfolio = (
            f"### About '{name}'\n"
            f"Built using **{tech_str}**, this project was engineered to: *{desc}*.\n\n"
            f"#### Engineering Highlights\n"
            f"- Structured clean, reusable UI modules and component hierarchies.\n"
            f"- Established highly efficient backend API protocols and data synchronization.\n"
            f"- Designed relational/NoSQL schemas focusing on database reliability."
        )

        # 4. STAR Interview Explanation
        star = {
            "situation": f"We wanted to build '{name}' as a solution to address: '{desc.rstrip('.')}'.",
            "task": f"My task was to design and implement the software architecture, select the tech stack ({tech_str}), and engineer the core operational logic.",
            "action": f"I set up state management and routing configurations, integrated database services, and thoroughly tested API connections to ensure 100% data reliability.",
            "result": f"Successfully launched the project on schedule, achieving modular stability and providing a fast, scalable interface for users."
        }

        return {
            "bullets": bullets,
            "linkedin": linkedin,
            "portfolio": portfolio,
            "star": star
        }
