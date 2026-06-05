import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from resume_builder.templates.base import BaseTemplate

class TwoColumnTemplate(BaseTemplate):
    def generate(self, data, pdf_filename, accent_color, font_scale, margin_size, **kwargs):
        def scale_spacer(w, h):
            return Spacer(w, h * font_scale)
            
        top_bottom_margin = margin_size - 2
        left_right_margin = margin_size * 1.3
        
        doc = SimpleDocTemplate(
            pdf_filename,
            pagesize=letter,
            leftMargin=left_right_margin,
            rightMargin=left_right_margin,
            topMargin=top_bottom_margin,
            bottomMargin=top_bottom_margin
        )
        
        width = 612 - (2 * left_right_margin)
        styles = getSampleStyleSheet()
        
        accent = colors.HexColor(accent_color)
        text_dark = colors.HexColor('#0F172A') # slate 900
        text_muted = colors.HexColor('#475569') # slate 600
        border_color = colors.HexColor('#CBD5E1') # slate 300
        
        # Typography styles
        name_style = ParagraphStyle(
            'TCName',
            fontName='Helvetica-Bold',
            fontSize=16 * font_scale,
            leading=18 * font_scale,
            textColor=accent,
            spaceAfter=4 * font_scale
        )
        
        sidebar_title_style = ParagraphStyle(
            'TCSideTitle',
            fontName='Helvetica-Bold',
            fontSize=9.5 * font_scale,
            leading=12 * font_scale,
            textColor=accent,
            spaceAfter=3 * font_scale
        )
        
        main_title_style = ParagraphStyle(
            'TCMainTitle',
            fontName='Helvetica-Bold',
            fontSize=10.5 * font_scale,
            leading=13 * font_scale,
            textColor=text_dark,
            spaceAfter=3 * font_scale
        )
        
        body_style = ParagraphStyle(
            'TCBody',
            fontName='Helvetica',
            fontSize=7.8 * font_scale,
            leading=10 * font_scale,
            textColor=text_dark
        )
        
        sidebar_body_style = ParagraphStyle(
            'TCSideBody',
            fontName='Helvetica',
            fontSize=7.6 * font_scale,
            leading=10 * font_scale,
            textColor=text_dark
        )
        
        bullet_style = ParagraphStyle(
            'TCBullet',
            parent=body_style,
            leftIndent=12 * font_scale,
            firstLineIndent=-8 * font_scale,
            spaceAfter=1 * font_scale
        )
        
        # --- LEFT COLUMN (SIDEBAR) STORY ---
        left_story = []
        
        personal = data.get("personal", {})
        name = personal.get("name", "SEJAL BHAGAT")
        left_story.append(Paragraph(name, name_style))
        left_story.append(scale_spacer(1, 4))
        
        # Contact info
        loc = personal.get("location", "")
        phone = personal.get("phone", "")
        email = personal.get("email", "")
        linkedin = personal.get("linkedin", {})
        github = personal.get("github", {})
        
        left_story.append(Paragraph("<b>CONTACT</b>", sidebar_title_style))
        if loc: left_story.append(Paragraph(f"📍 {loc}", sidebar_body_style))
        if phone: left_story.append(Paragraph(f"📞 {phone}", sidebar_body_style))
        if email: left_story.append(Paragraph(f"✉️ <a href='mailto:{email}'><font color='{accent_color}'>{email}</font></a>", sidebar_body_style))
        if linkedin.get("display"): left_story.append(Paragraph(f"🔗 <a href='{linkedin.get('url','')}'><font color='{accent_color}'>{linkedin.get('display')}</font></a>", sidebar_body_style))
        if github.get("display"): left_story.append(Paragraph(f"💻 <a href='{github.get('url','')}'><font color='{accent_color}'>{github.get('display')}</font></a>", sidebar_body_style))
        left_story.append(scale_spacer(1, 6))
        
        # Technical skills
        skills = data.get("technical_skills", {})
        if skills:
            left_story.append(Paragraph("<b>SKILLS</b>", sidebar_title_style))
            for cat_name, cat_val in skills.items():
                left_story.append(Paragraph(f"<b>{cat_name}:</b>", sidebar_body_style))
                left_story.append(Paragraph(cat_val, sidebar_body_style))
                left_story.append(scale_spacer(1, 2))
            left_story.append(scale_spacer(1, 4))
            
        # Education
        education = data.get("education", [])
        if education:
            left_story.append(Paragraph("<b>EDUCATION</b>", sidebar_title_style))
            for edu in education:
                deg = edu.get("degree", "")
                inst = edu.get("institution", "")
                det = edu.get("details", "")
                per = edu.get("period", "")
                
                left_story.append(Paragraph(f"<b>{deg}</b>", sidebar_body_style))
                left_story.append(Paragraph(inst, sidebar_body_style))
                if per: left_story.append(Paragraph(per, sidebar_body_style))
                if det: left_story.append(Paragraph(det, ParagraphStyle('TCSideEduDet', parent=sidebar_body_style, textColor=text_muted)))
                left_story.append(scale_spacer(1, 3))
            left_story.append(scale_spacer(1, 4))

        # --- RIGHT COLUMN (MAIN) STORY ---
        right_story = []
        
        def add_main_header(title):
            p = Paragraph(title.upper(), main_title_style)
            t = Table([[p]], colWidths=[width * 0.65 - 10])
            t.setStyle(TableStyle([
                ('LINEBELOW', (0,0), (-1,-1), 1.0, accent),
                ('TOPPADDING', (0,0), (-1,-1), 2),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ]))
            right_story.append(t)
            right_story.append(scale_spacer(1, 3))
            
        def clean_bullet(text):
            if not text:
                return ""
            text = text.strip()
            for prefix in ["&bull;", "•", "-", "*"]:
                if text.startswith(prefix):
                    text = text[len(prefix):].strip()
            return text
            
        # Summary
        summary = data.get("summary", "")
        if summary:
            add_main_header("Profile Summary")
            right_story.append(Paragraph(summary, body_style))
            right_story.append(scale_spacer(1, 5))
            
        # Experience
        experience = data.get("experience", [])
        if experience:
            add_main_header("Experience")
            for job in experience:
                role = job.get("role", "")
                company = job.get("company", "")
                location = job.get("location", "")
                period = job.get("period", "")
                
                left_t = f"<b>{role}</b> &mdash; {company}" + (f" ({location})" if location else "")
                left_p = Paragraph(left_t, body_style)
                right_p = Paragraph(f"<b>{period}</b>", ParagraphStyle('TCExtDate', parent=body_style, alignment=2))
                
                t = Table([[left_p, right_p]], colWidths=[width * 0.48, width * 0.17])
                t.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('LEFTPADDING', (0,0), (-1,-1), 0),
                    ('RIGHTPADDING', (0,0), (-1,-1), 0),
                    ('TOPPADDING', (0,0), (-1,-1), 0.5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 0.5),
                ]))
                right_story.append(t)
                
                techs = job.get("technologies", "")
                if techs:
                    right_story.append(Paragraph(f"<b>Tech:</b> {techs}", ParagraphStyle('TCTech', parent=body_style, leftIndent=6*font_scale, fontName='Helvetica-Oblique', textColor=text_muted)))
                    
                for bullet in job.get("bullets", []):
                    cleaned = clean_bullet(bullet)
                    right_story.append(Paragraph(f"&bull;&nbsp;&nbsp;{cleaned}", bullet_style))
                right_story.append(scale_spacer(1, 3))
            right_story.append(scale_spacer(1, 2))
            
        # Projects
        projects = data.get("projects", [])
        if projects:
            add_main_header("Projects")
            for proj in projects:
                title = proj.get("title", "")
                link = proj.get("link", "")
                date = proj.get("date", "")
                tools = proj.get("tools", "")
                
                left_t = f"<b>{title}</b>" + (f" | <a href='{link}'><font color='{accent_color}'>Link</font></a>" if link else "")
                left_p = Paragraph(left_t, body_style)
                right_p = Paragraph(f"<b>{date}</b>", ParagraphStyle('TCProjDate', parent=body_style, alignment=2))
                
                t = Table([[left_p, right_p]], colWidths=[width * 0.48, width * 0.17])
                t.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('LEFTPADDING', (0,0), (-1,-1), 0),
                    ('RIGHTPADDING', (0,0), (-1,-1), 0),
                    ('TOPPADDING', (0,0), (-1,-1), 0.5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 0.5),
                ]))
                right_story.append(t)
                
                if tools:
                    right_story.append(Paragraph(f"<b>Tech:</b> {tools}", ParagraphStyle('TCTools', parent=body_style, leftIndent=6*font_scale, fontName='Helvetica-Oblique', textColor=text_muted)))
                    
                for bullet in proj.get("bullets", []):
                    cleaned = clean_bullet(bullet)
                    right_story.append(Paragraph(f"&bull;&nbsp;&nbsp;{cleaned}", bullet_style))
                right_story.append(scale_spacer(1, 3))
            right_story.append(scale_spacer(1, 2))
            
        # Achievements
        achievements = data.get("achievements", [])
        if achievements:
            add_main_header("Achievements")
            for achievement in achievements:
                cleaned = clean_bullet(achievement)
                right_story.append(Paragraph(f"&bull;&nbsp;&nbsp;{cleaned}", bullet_style))
            right_story.append(scale_spacer(1, 4))
            
        # Positions of Responsibility
        por = data.get("position_of_responsibility", [])
        if por:
            add_main_header("Positions of Responsibility")
            for item in por:
                role = item.get("role", "")
                period = item.get("period", "")
                
                left_p = Paragraph(f"<b>{role}</b>", body_style)
                right_p = Paragraph(f"<b>{period}</b>", ParagraphStyle('TCPorDate', parent=body_style, alignment=2))
                
                t = Table([[left_p, right_p]], colWidths=[width * 0.48, width * 0.17])
                t.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('LEFTPADDING', (0,0), (-1,-1), 0),
                    ('RIGHTPADDING', (0,0), (-1,-1), 0),
                    ('TOPPADDING', (0,0), (-1,-1), 0.5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 0.5),
                ]))
                right_story.append(t)
                for bullet in item.get("bullets", []):
                    cleaned = clean_bullet(bullet)
                    right_story.append(Paragraph(f"&bull;&nbsp;&nbsp;{cleaned}", bullet_style))
                right_story.append(scale_spacer(1, 3))

        # --- LAYOUT MASTER TABLE ---
        # left sidebar has width * 0.32, gap has width * 0.03, right column has width * 0.65
        main_table = Table([[left_story, "", right_story]], colWidths=[width * 0.31, width * 0.04, width * 0.65])
        main_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('LINEBEFORE', (2,0), (2,-1), 0.75, border_color), # Vertical border separator
            ('LEFTPADDING', (2,0), (2,-1), 10 * font_scale), # Padding inside right column
        ]))
        
        story_list = [main_table]
        
        try:
            doc.build(story_list)
        except Exception as e:
            return False, str(e)
            
        return True, None
