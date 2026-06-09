import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from resume_builder.templates.base import BaseTemplate

class ModernTemplate(BaseTemplate):
    def generate(self, data, pdf_filename, accent_color, font_scale, margin_size, **kwargs):
        def scale_spacer(w, h):
            return Spacer(w, h * font_scale)
            
        top_bottom_margin = margin_size
        left_right_margin = margin_size * 1.5
        
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
        text_dark = colors.HexColor('#1E293B') # Slate 800
        text_muted = colors.HexColor('#64748B') # Slate 500
        
        name_style = ParagraphStyle(
            'ModernNameStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=22 * font_scale,
            leading=25 * font_scale,
            textColor=accent,
            alignment=0 # Left aligned
        )
        
        contact_style = ParagraphStyle(
            'ModernContactStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5 * font_scale,
            leading=11.5 * font_scale,
            textColor=text_dark,
            alignment=0
        )
        
        section_title_style = ParagraphStyle(
            'ModernSectionTitleStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11 * font_scale,
            leading=13 * font_scale,
            textColor=text_dark,
            spaceAfter=0
        )
        
        body_style = ParagraphStyle(
            'ModernBodyStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.2 * font_scale,
            leading=10.8 * font_scale,
            textColor=text_dark
        )
        
        bold_body_style = ParagraphStyle(
            'ModernBoldBodyStyle',
            parent=body_style,
            fontName='Helvetica-Bold'
        )
        
        bullet_style = ParagraphStyle(
            'ModernBulletStyle',
            parent=body_style,
            leftIndent=16 * font_scale,
            firstLineIndent=-8 * font_scale,
            spaceAfter=1 * font_scale
        )
        
        story = []
        
        # --- HEADER ---
        personal = data.get("personal", {})
        name = personal.get("name", "YOUR NAME")
        story.append(Paragraph(name, name_style))
        story.append(scale_spacer(1, 2))
        
        # Contact info on 2 columns
        loc = personal.get("location", "")
        phone = personal.get("phone", "")
        left_text = f"{loc}" + (f" &nbsp;|&nbsp; {phone}" if phone and loc else (phone if phone else ""))
        left_p = Paragraph(left_text, contact_style)
        
        email = personal.get("email", "")
        linkedin = personal.get("linkedin", {})
        github = personal.get("github", {})
        
        links = []
        if email: links.append(f"<a href='mailto:{email}'><font color='{accent_color}'>{email}</font></a>")
        if linkedin.get("display"): links.append(f"<a href='{linkedin.get('url', '')}'><font color='{accent_color}'>{linkedin.get('display')}</font></a>")
        if github.get("display"): links.append(f"<a href='{github.get('url', '')}'><font color='{accent_color}'>{github.get('display')}</font></a>")
        
        right_text = " &nbsp;|&nbsp; ".join(links)
        right_p = Paragraph(right_text, ParagraphStyle('ModernRightContact', parent=contact_style, alignment=2))
        
        t = Table([[left_p, right_p]], colWidths=[width * 0.45, width * 0.55])
        t.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(t)
        story.append(scale_spacer(1, 4))
        
        # --- HELPERS ---
        def add_section_header(title):
            p = Paragraph(title.upper(), section_title_style)
            # Left accent border table
            t = Table([["", p]], colWidths=[3, width - 3])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (0,0), accent),
                ('TOPPADDING', (0,0), (-1,-1), 1),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('LEFTPADDING', (1,0), (1,0), 6),
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
            story.append(scale_spacer(1, 4))
            
        # --- EXPERIENCE ---
        experience = data.get("experience", [])
        if experience:
            add_section_header("Professional Experience")
            for job in experience:
                role = job.get("role", "")
                company = job.get("company", "")
                location = job.get("location", "")
                period = job.get("period", "")
                
                left_text = f"<b>{role}</b> &mdash; <font color='{accent_color}'>{company}</font>" + (f" &nbsp;|&nbsp; <i>{location}</i>" if location else "")
                left_p = Paragraph(left_text, body_style)
                right_p = Paragraph(f"<b>{period}</b>", ParagraphStyle('ModernDateRight', parent=body_style, alignment=2))
                
                t = Table([[left_p, right_p]], colWidths=[width * 0.75, width * 0.25])
                t.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('LEFTPADDING', (0,0), (-1,-1), 0),
                    ('RIGHTPADDING', (0,0), (-1,-1), 0),
                    ('TOPPADDING', (0,0), (-1,-1), 1),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 1),
                ]))
                story.append(t)
                
                techs = job.get("technologies", "")
                if techs:
                    story.append(Paragraph(f"<b>Technologies:</b> {techs}", ParagraphStyle('ModernTech', parent=body_style, leftIndent=8*font_scale, fontName='Helvetica-Oblique', textColor=text_muted)))
                    
                for bullet in job.get("bullets", []):
                    cleaned = clean_bullet(bullet)
                    story.append(Paragraph(f"&bull;&nbsp;&nbsp;{cleaned}", bullet_style))
                story.append(scale_spacer(1, 3))
            story.append(scale_spacer(1, 2))

        # --- PROJECTS ---
        projects = data.get("projects", [])
        if projects:
            add_section_header("Projects")
            for proj in projects:
                title = proj.get("title", "")
                link = proj.get("link", "")
                date = proj.get("date", "")
                tools = proj.get("tools", "")
                
                left_text = f"<b>{title}</b>" + (f" &nbsp;|&nbsp; <a href='{link}'><font color='{accent_color}'>Link</font></a>" if link else "")
                left_p = Paragraph(left_text, body_style)
                right_p = Paragraph(f"<b>{date}</b>", ParagraphStyle('ModernProjDateRight', parent=body_style, alignment=2))
                
                t = Table([[left_p, right_p]], colWidths=[width * 0.75, width * 0.25])
                t.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('LEFTPADDING', (0,0), (-1,-1), 0),
                    ('RIGHTPADDING', (0,0), (-1,-1), 0),
                    ('TOPPADDING', (0,0), (-1,-1), 1),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 1),
                ]))
                story.append(t)
                
                if tools:
                    story.append(Paragraph(f"<b>Tools:</b> {tools}", ParagraphStyle('ModernTools', parent=body_style, leftIndent=8*font_scale, fontName='Helvetica-Oblique', textColor=text_muted)))
                    
                for bullet in proj.get("bullets", []):
                    cleaned = clean_bullet(bullet)
                    story.append(Paragraph(f"&bull;&nbsp;&nbsp;{cleaned}", bullet_style))
                story.append(scale_spacer(1, 3))
            story.append(scale_spacer(1, 2))

        # --- TECHNICAL SKILLS ---
        technical_skills = data.get("technical_skills", {})
        if technical_skills:
            add_section_header("Technical Skills")
            for skill_name, skill_val in technical_skills.items():
                p_text = f"&bull;&nbsp;&nbsp;<b>{skill_name}:</b> {skill_val}"
                story.append(Paragraph(p_text, ParagraphStyle('ModernSkillList', parent=body_style, leftIndent=8*font_scale, spaceAfter=2*font_scale)))
            story.append(scale_spacer(1, 3))
            
        # --- CERTIFICATIONS & ACHIEVEMENTS ---
        achievements = data.get("achievements", [])
        certifications = data.get("certifications", [])
        if achievements or certifications:
            if achievements and certifications:
                header_title = "Certifications & Achievements"
            elif certifications:
                header_title = "Certifications"
            else:
                header_title = "Achievements"
            add_section_header(header_title)
            for cert in certifications:
                cleaned = clean_bullet(cert)
                story.append(Paragraph(f"&bull;&nbsp;&nbsp;{cleaned}", ParagraphStyle('ModernAch', parent=body_style, leftIndent=12*font_scale, firstLineIndent=-8*font_scale, spaceAfter=2*font_scale)))
            for achievement in achievements:
                cleaned = clean_bullet(achievement)
                story.append(Paragraph(f"&bull;&nbsp;&nbsp;{cleaned}", ParagraphStyle('ModernAch', parent=body_style, leftIndent=12*font_scale, firstLineIndent=-8*font_scale, spaceAfter=2*font_scale)))
            story.append(scale_spacer(1, 3))

        # --- EDUCATION ---
        education = data.get("education", [])
        if education:
            add_section_header("Education")
            for edu in education:
                deg = edu.get("degree", "")
                inst = edu.get("institution", "")
                det = edu.get("details", "")
                per = edu.get("period", "")
                
                left_text = f"<b>{deg}</b>" + (f" &nbsp;|&nbsp; <i>{inst}</i>" if inst else "")
                left_p = Paragraph(left_text, body_style)
                right_p = Paragraph(f"<b>{per}</b>", ParagraphStyle('ModernEduDateRight', parent=body_style, alignment=2))
                
                t = Table([[left_p, right_p]], colWidths=[width * 0.75, width * 0.25])
                t.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('LEFTPADDING', (0,0), (-1,-1), 0),
                    ('RIGHTPADDING', (0,0), (-1,-1), 0),
                    ('TOPPADDING', (0,0), (-1,-1), 1),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 1),
                ]))
                story.append(t)
                if det:
                    story.append(Paragraph(det, ParagraphStyle('ModernEduDet', parent=body_style, leftIndent=8*font_scale, textColor=text_muted)))
                story.append(scale_spacer(1, 2))
            story.append(scale_spacer(1, 2))

        # --- POSITION OF RESPONSIBILITY ---
        por = data.get("position_of_responsibility", [])
        if por:
            add_section_header("Position of Responsibility")
            for item in por:
                role = item.get("role", "")
                period = item.get("period", "")
                
                left_p = Paragraph(f"<b>{role}</b>", body_style)
                right_p = Paragraph(f"<b>{period}</b>", ParagraphStyle('ModernPorDateRight', parent=body_style, alignment=2))
                
                t = Table([[left_p, right_p]], colWidths=[width * 0.75, width * 0.25])
                t.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('LEFTPADDING', (0,0), (-1,-1), 0),
                    ('RIGHTPADDING', (0,0), (-1,-1), 0),
                    ('TOPPADDING', (0,0), (-1,-1), 1),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 1),
                ]))
                story.append(t)
                for bullet in item.get("bullets", []):
                    cleaned = clean_bullet(bullet)
                    story.append(Paragraph(f"&bull;&nbsp;&nbsp;{cleaned}", bullet_style))
                story.append(scale_spacer(1, 3))
                
        try:
            doc.build(story)
        except Exception as e:
            return False, str(e)
            
        return True, None
