import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from resume_builder.templates.base import BaseTemplate

class CreativeTemplate(BaseTemplate):
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
        text_dark = colors.HexColor('#0F172A') # slate 900
        text_muted = colors.HexColor('#475569') # slate 600
        
        name_style = ParagraphStyle(
            'CreativeNameStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=24 * font_scale,
            leading=28 * font_scale,
            textColor=colors.white,
            alignment=1 # Centered inside banner
        )
        
        contact_style = ParagraphStyle(
            'CreativeContactStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5 * font_scale,
            leading=12 * font_scale,
            textColor=colors.white,
            alignment=1
        )
        
        section_title_style = ParagraphStyle(
            'CreativeSectionTitleStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11 * font_scale,
            leading=13 * font_scale,
            textColor=accent,
            spaceAfter=0
        )
        
        body_style = ParagraphStyle(
            'CreativeBodyStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.2 * font_scale,
            leading=11 * font_scale,
            textColor=text_dark
        )
        
        bullet_style = ParagraphStyle(
            'CreativeBulletStyle',
            parent=body_style,
            leftIndent=18 * font_scale,
            firstLineIndent=-10 * font_scale,
            spaceAfter=1.5 * font_scale
        )
        
        story = []
        
        # --- HEADER BANNER ---
        personal = data.get("personal", {})
        name = personal.get("name", "SEJAL BHAGAT").upper()
        
        loc = personal.get("location", "")
        phone = personal.get("phone", "")
        email = personal.get("email", "")
        linkedin = personal.get("linkedin", {})
        github = personal.get("github", {})
        
        contacts = []
        if loc: contacts.append(loc)
        if phone: contacts.append(phone)
        if email: contacts.append(email)
        if linkedin.get("display"): contacts.append(linkedin.get("display"))
        if github.get("display"): contacts.append(github.get("display"))
        
        contact_text = " &nbsp;&bull;&nbsp; ".join(contacts)
        
        banner_content = [
            Paragraph(name, name_style),
            scale_spacer(1, 3),
            Paragraph(contact_text, contact_style)
        ]
        
        # Inner table to hold the banner elements with colored background
        banner_table = Table([[banner_content]], colWidths=[width])
        banner_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), accent),
            ('TOPPADDING', (0,0), (-1,-1), 12 * font_scale),
            ('BOTTOMPADDING', (0,0), (-1,-1), 12 * font_scale),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(banner_table)
        story.append(scale_spacer(1, 4))
        
        # --- HELPERS ---
        def add_section_header(title):
            p = Paragraph(title.upper(), section_title_style)
            # Underline with colored divider bar
            t = Table([[p]], colWidths=[width])
            t.setStyle(TableStyle([
                ('LINEBELOW', (0,0), (-1,-1), 1.25, accent),
                ('TOPPADDING', (0,0), (-1,-1), 2),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(t)
            story.append(scale_spacer(1, 4))
            
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
            add_section_header("About Me")
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
                
                left_text = f"<b>{role}</b> at <b><font color='{accent_color}'>{company}</font></b>" + (f" &nbsp;|&nbsp; <i>{location}</i>" if location else "")
                left_p = Paragraph(left_text, body_style)
                right_p = Paragraph(f"<b>{period}</b>", ParagraphStyle('CreativeDateRight', parent=body_style, alignment=2))
                
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
                    story.append(Paragraph(f"<b>Technologies:</b> {techs}", ParagraphStyle('CreativeTech', parent=body_style, leftIndent=10*font_scale, textColor=text_muted)))
                    
                for bullet in job.get("bullets", []):
                    cleaned = clean_bullet(bullet)
                    story.append(Paragraph(f"<font color='{accent_color}'>&bull;</font>&nbsp;&nbsp;{cleaned}", bullet_style))
                story.append(scale_spacer(1, 3))
            story.append(scale_spacer(1, 2))

        # --- PROJECTS ---
        projects = data.get("projects", [])
        if projects:
            add_section_header("Featured Projects")
            for proj in projects:
                title = proj.get("title", "")
                link = proj.get("link", "")
                date = proj.get("date", "")
                tools = proj.get("tools", "")
                
                left_text = f"<b>{title}</b>" + (f" &nbsp;|&nbsp; <a href='{link}'><font color='{accent_color}'>Demo Link</font></a>" if link else "")
                left_p = Paragraph(left_text, body_style)
                right_p = Paragraph(f"<b>{date}</b>", ParagraphStyle('CreativeProjDateRight', parent=body_style, alignment=2))
                
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
                    story.append(Paragraph(f"<b>Tools:</b> {tools}", ParagraphStyle('CreativeTools', parent=body_style, leftIndent=10*font_scale, textColor=text_muted)))
                    
                for bullet in proj.get("bullets", []):
                    cleaned = clean_bullet(bullet)
                    story.append(Paragraph(f"<font color='{accent_color}'>&bull;</font>&nbsp;&nbsp;{cleaned}", bullet_style))
                story.append(scale_spacer(1, 3))
            story.append(scale_spacer(1, 2))

        # --- TECHNICAL SKILLS ---
        technical_skills = data.get("technical_skills", {})
        if technical_skills:
            add_section_header("Technical Skills")
            for skill_name, skill_val in technical_skills.items():
                p_text = f"<font color='{accent_color}'>&bull;</font>&nbsp;&nbsp;<b>{skill_name}:</b> {skill_val}"
                story.append(Paragraph(p_text, ParagraphStyle('CreativeSkillList', parent=body_style, leftIndent=10*font_scale, spaceAfter=2.5*font_scale)))
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
                header_title = "Key Achievements"
            add_section_header(header_title)
            for cert in certifications:
                cleaned = clean_bullet(cert)
                story.append(Paragraph(f"<font color='{accent_color}'>&bull;</font>&nbsp;&nbsp;{cleaned}", ParagraphStyle('CreativeAch', parent=body_style, leftIndent=14*font_scale, firstLineIndent=-8*font_scale, spaceAfter=2*font_scale)))
            for achievement in achievements:
                cleaned = clean_bullet(achievement)
                story.append(Paragraph(f"<font color='{accent_color}'>&bull;</font>&nbsp;&nbsp;{cleaned}", ParagraphStyle('CreativeAch', parent=body_style, leftIndent=14*font_scale, firstLineIndent=-8*font_scale, spaceAfter=2*font_scale)))
            story.append(scale_spacer(1, 3))

        # --- EDUCATION ---
        education = data.get("education", [])
        if education:
            add_section_header("Education Background")
            for edu in education:
                deg = edu.get("degree", "")
                inst = edu.get("institution", "")
                det = edu.get("details", "")
                per = edu.get("period", "")
                
                left_text = f"<b>{deg}</b> &mdash; <i>{inst}</i>"
                left_p = Paragraph(left_text, body_style)
                right_p = Paragraph(f"<b>{per}</b>", ParagraphStyle('CreativeEduDateRight', parent=body_style, alignment=2))
                
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
                    story.append(Paragraph(det, ParagraphStyle('CreativeEduDet', parent=body_style, leftIndent=10*font_scale, textColor=text_muted)))
                story.append(scale_spacer(1, 2))
            story.append(scale_spacer(1, 2))

        # --- POSITION OF RESPONSIBILITY ---
        por = data.get("position_of_responsibility", [])
        if por:
            add_section_header("Positions of Responsibility")
            for item in por:
                role = item.get("role", "")
                period = item.get("period", "")
                
                left_p = Paragraph(f"<b>{role}</b>", body_style)
                right_p = Paragraph(f"<b>{period}</b>", ParagraphStyle('CreativePorDateRight', parent=body_style, alignment=2))
                
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
                    story.append(Paragraph(f"<font color='{accent_color}'>&bull;</font>&nbsp;&nbsp;{cleaned}", bullet_style))
                story.append(scale_spacer(1, 3))
                
        try:
            doc.build(story)
        except Exception as e:
            return False, str(e)
            
        return True, None
