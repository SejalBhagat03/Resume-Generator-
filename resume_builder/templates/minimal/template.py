import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from resume_builder.templates.base import BaseTemplate

class MinimalTemplate(BaseTemplate):
    def generate(self, data, pdf_filename, accent_color, font_scale, margin_size, **kwargs):
        def scale_spacer(w, h):
            return Spacer(w, h * font_scale)
            
        # Compact margins (Standard is 20, minimal defaults to 16)
        top_bottom_margin = margin_size - 4
        left_right_margin = margin_size * 1.4
        
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
        
        primary_color = colors.HexColor('#1E293B') # Slate 800
        accent = colors.HexColor(accent_color)
        text_muted = colors.HexColor('#64748B') # Slate 500
        
        name_style = ParagraphStyle(
            'MinimalNameStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=16 * font_scale,
            leading=18 * font_scale,
            textColor=primary_color,
            alignment=1 # Centered
        )
        
        contact_style = ParagraphStyle(
            'MinimalContactStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.0 * font_scale,
            leading=11 * font_scale,
            textColor=text_muted,
            alignment=1
        )
        
        section_title_style = ParagraphStyle(
            'MinimalSectionTitleStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9.5 * font_scale,
            leading=11.5 * font_scale,
            textColor=primary_color,
            spaceAfter=0
        )
        
        body_style = ParagraphStyle(
            'MinimalBodyStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=7.8 * font_scale,
            leading=10 * font_scale,
            textColor=primary_color
        )
        
        bullet_style = ParagraphStyle(
            'MinimalBulletStyle',
            parent=body_style,
            leftIndent=14 * font_scale,
            firstLineIndent=-8 * font_scale,
            spaceAfter=1 * font_scale
        )
        
        story = []
        
        # --- HEADER ---
        personal = data.get("personal", {})
        name = personal.get("name", "SEJAL BHAGAT").upper()
        story.append(Paragraph(name, name_style))
        story.append(scale_spacer(1, 2))
        
        loc = personal.get("location", "")
        phone = personal.get("phone", "")
        email = personal.get("email", "")
        linkedin = personal.get("linkedin", {})
        github = personal.get("github", {})
        
        contacts = []
        if loc: contacts.append(loc)
        if phone: contacts.append(phone)
        if email: contacts.append(f"<a href='mailto:{email}'><font color='{accent_color}'>{email}</font></a>")
        if linkedin.get("display"): contacts.append(f"<a href='{linkedin.get('url', '')}'><font color='{accent_color}'>{linkedin.get('display')}</font></a>")
        if github.get("display"): contacts.append(f"<a href='{github.get('url', '')}'><font color='{accent_color}'>{github.get('display')}</font></a>")
        
        contact_text = " &nbsp;&bull;&nbsp; ".join(contacts)
        story.append(Paragraph(contact_text, contact_style))
        story.append(scale_spacer(1, 3))
        
        # --- HELPERS ---
        def add_section_header(title):
            p = Paragraph(title.upper(), section_title_style)
            # Thin center-colored divider
            t = Table([[p]], colWidths=[width])
            t.setStyle(TableStyle([
                ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
                ('TOPPADDING', (0,0), (-1,-1), 2),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(t)
            story.append(scale_spacer(1, 3))
            
        def clean_bullet(text):
            if not text:
                return ""
            text = text.strip()
            for prefix in ["&bull;", "•", "-", "*"]:
                if text.startswith(prefix):
                    text = text[len(prefix):].strip()
            return text
            
        # --- SUMMARY ---
        summary_text = data.get("summary", "")
        if summary_text:
            add_section_header("Summary")
            story.append(Paragraph(summary_text, body_style))
            story.append(scale_spacer(1, 3))
            
        # --- EXPERIENCE ---
        experience = data.get("experience", [])
        if experience:
            add_section_header("Experience")
            for job in experience:
                role = job.get("role", "")
                company = job.get("company", "")
                location = job.get("location", "")
                period = job.get("period", "")
                
                left_text = f"<b>{role}</b> &mdash; {company}" + (f" ({location})" if location else "")
                left_p = Paragraph(left_text, body_style)
                right_p = Paragraph(f"<b>{period}</b>", ParagraphStyle('MinDateRight', parent=body_style, alignment=2))
                
                t = Table([[left_p, right_p]], colWidths=[width * 0.75, width * 0.25])
                t.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('LEFTPADDING', (0,0), (-1,-1), 0),
                    ('RIGHTPADDING', (0,0), (-1,-1), 0),
                    ('TOPPADDING', (0,0), (-1,-1), 0.5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 0.5),
                ]))
                story.append(t)
                
                techs = job.get("technologies", "")
                if techs:
                    story.append(Paragraph(f"<b>Tech:</b> {techs}", ParagraphStyle('MinTech', parent=body_style, leftIndent=6*font_scale, fontName='Helvetica-Oblique', textColor=text_muted)))
                    
                for bullet in job.get("bullets", []):
                    cleaned = clean_bullet(bullet)
                    story.append(Paragraph(f"&bull;&nbsp;&nbsp;{cleaned}", bullet_style))
                story.append(scale_spacer(1, 2))
            story.append(scale_spacer(1, 1))

        # --- PROJECTS ---
        projects = data.get("projects", [])
        if projects:
            add_section_header("Projects")
            for proj in projects:
                title = proj.get("title", "")
                link = proj.get("link", "")
                date = proj.get("date", "")
                tools = proj.get("tools", "")
                
                left_text = f"<b>{title}</b>" + (f" | <a href='{link}'><font color='{accent_color}'>Link</font></a>" if link else "")
                left_p = Paragraph(left_text, body_style)
                right_p = Paragraph(f"<b>{date}</b>", ParagraphStyle('MinProjDateRight', parent=body_style, alignment=2))
                
                t = Table([[left_p, right_p]], colWidths=[width * 0.75, width * 0.25])
                t.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('LEFTPADDING', (0,0), (-1,-1), 0),
                    ('RIGHTPADDING', (0,0), (-1,-1), 0),
                    ('TOPPADDING', (0,0), (-1,-1), 0.5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 0.5),
                ]))
                story.append(t)
                
                if tools:
                    story.append(Paragraph(f"<b>Tech:</b> {tools}", ParagraphStyle('MinTools', parent=body_style, leftIndent=6*font_scale, fontName='Helvetica-Oblique', textColor=text_muted)))
                    
                for bullet in proj.get("bullets", []):
                    cleaned = clean_bullet(bullet)
                    story.append(Paragraph(f"&bull;&nbsp;&nbsp;{cleaned}", bullet_style))
                story.append(scale_spacer(1, 2))
            story.append(scale_spacer(1, 1))

        # --- TECHNICAL SKILLS ---
        technical_skills = data.get("technical_skills", {})
        if technical_skills:
            add_section_header("Skills")
            for skill_name, skill_val in technical_skills.items():
                p_text = f"<b>{skill_name}:</b> {skill_val}"
                story.append(Paragraph(p_text, ParagraphStyle('MinSkillList', parent=body_style, leftIndent=6*font_scale, spaceAfter=1.5*font_scale)))
            story.append(scale_spacer(1, 2))
            
        # --- ACHIEVEMENTS ---
        achievements = data.get("achievements", [])
        if achievements:
            add_section_header("Achievements")
            for achievement in achievements:
                cleaned = clean_bullet(achievement)
                story.append(Paragraph(f"&bull;&nbsp;&nbsp;{cleaned}", bullet_style))
            story.append(scale_spacer(1, 2))

        # --- EDUCATION ---
        education = data.get("education", [])
        if education:
            add_section_header("Education")
            for edu in education:
                deg = edu.get("degree", "")
                inst = edu.get("institution", "")
                det = edu.get("details", "")
                per = edu.get("period", "")
                
                left_text = f"<b>{deg}</b> &mdash; <i>{inst}</i>"
                left_p = Paragraph(left_text, body_style)
                right_p = Paragraph(f"<b>{per}</b>", ParagraphStyle('MinEduDateRight', parent=body_style, alignment=2))
                
                t = Table([[left_p, right_p]], colWidths=[width * 0.75, width * 0.25])
                t.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('LEFTPADDING', (0,0), (-1,-1), 0),
                    ('RIGHTPADDING', (0,0), (-1,-1), 0),
                    ('TOPPADDING', (0,0), (-1,-1), 0.5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 0.5),
                ]))
                story.append(t)
                if det:
                    story.append(Paragraph(det, ParagraphStyle('MinEduDet', parent=body_style, leftIndent=6*font_scale, textColor=text_muted)))
                story.append(scale_spacer(1, 1.5))
            story.append(scale_spacer(1, 1))

        # --- POSITION OF RESPONSIBILITY ---
        por = data.get("position_of_responsibility", [])
        if por:
            add_section_header("Responsibility")
            for item in por:
                role = item.get("role", "")
                period = item.get("period", "")
                
                left_p = Paragraph(f"<b>{role}</b>", body_style)
                right_p = Paragraph(f"<b>{period}</b>", ParagraphStyle('MinPorDateRight', parent=body_style, alignment=2))
                
                t = Table([[left_p, right_p]], colWidths=[width * 0.75, width * 0.25])
                t.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('LEFTPADDING', (0,0), (-1,-1), 0),
                    ('RIGHTPADDING', (0,0), (-1,-1), 0),
                    ('TOPPADDING', (0,0), (-1,-1), 0.5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 0.5),
                ]))
                story.append(t)
                for bullet in item.get("bullets", []):
                    cleaned = clean_bullet(bullet)
                    story.append(Paragraph(f"&bull;&nbsp;&nbsp;{cleaned}", bullet_style))
                story.append(scale_spacer(1, 2))
                
        try:
            doc.build(story)
        except Exception as e:
            return False, str(e)
            
        return True, None
