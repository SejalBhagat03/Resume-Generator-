import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from resume_builder.templates.base import BaseTemplate

class AtsProfessionalTemplate(BaseTemplate):
    def generate(self, data, pdf_filename, accent_color, font_scale, margin_size, spacing_scale=1.0, padding_scale=1.0, **kwargs):
        def scale_spacer(w, h):
            return Spacer(w, h * font_scale * spacing_scale)
            
        # Standard margins for ATS (1 inch is 72, standard is 54)
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
        
        # Plain black and white theme for maximum parser compatibility
        primary_color = colors.HexColor('#000000')
        divider_color = colors.HexColor('#333333')
        
        name_style = ParagraphStyle(
            'AtsNameStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=18 * font_scale,
            leading=21 * font_scale,
            textColor=primary_color,
            alignment=0 # Left aligned for ATS
        )
        
        contact_style = ParagraphStyle(
            'AtsContactStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5 * font_scale,
            leading=11 * font_scale,
            textColor=primary_color,
            alignment=0
        )
        
        section_title_style = ParagraphStyle(
            'AtsSectionTitleStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10 * font_scale,
            leading=12 * font_scale,
            textColor=primary_color,
            spaceAfter=2 * font_scale
        )
        
        body_style = ParagraphStyle(
            'AtsBodyStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.0 * font_scale,
            leading=10.5 * font_scale,
            textColor=primary_color
        )
        
        bold_body_style = ParagraphStyle(
            'AtsBoldBodyStyle',
            parent=body_style,
            fontName='Helvetica-Bold'
        )
        
        bullet_style = ParagraphStyle(
            'AtsBulletStyle',
            parent=body_style,
            leftIndent=15 * font_scale,
            firstLineIndent=-8 * font_scale,
            spaceAfter=1 * font_scale * padding_scale
        )
        
        story = []
        
        # --- HEADER ---
        personal = data.get("personal", {})
        name = personal.get("name", "").upper()
        story.append(Paragraph(name, name_style))
        story.append(scale_spacer(1, 2))
        
        # Clean comma-separated header text
        loc = personal.get("location", "")
        phone = personal.get("phone", "")
        email = personal.get("email", "")
        
        contacts = []
        if loc: contacts.append(loc)
        if phone: contacts.append(phone)
        if email: contacts.append(email)
        
        linkedin = personal.get("linkedin", {})
        if linkedin.get("display"): contacts.append(linkedin.get("display"))
        github = personal.get("github", {})
        if github.get("display"): contacts.append(github.get("display"))
        
        contact_text = " &nbsp;|&nbsp; ".join(contacts)
        story.append(Paragraph(contact_text, contact_style))
        story.append(scale_spacer(1, 4))
        
        # --- HELPERS ---
        def add_section_header(title):
            p = Paragraph(title.upper(), section_title_style)
            # Solid line under section headers
            t = Table([[p]], colWidths=[width])
            t.setStyle(TableStyle([
                ('LINEBELOW', (0,0), (-1,-1), 0.5, divider_color),
                ('TOPPADDING', (0,0), (-1,-1), 1),
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
                
                left_text = f"<b>{role}</b> &mdash; {company}" + (f" ({location})" if location else "")
                
                # ATS uses standard tables for aligning dates to the right
                left_p = Paragraph(left_text, body_style)
                right_p = Paragraph(f"<b>{period}</b>", ParagraphStyle('DateRight', parent=body_style, alignment=2))
                
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
                    story.append(Paragraph(f"<b>Technologies:</b> {techs}", ParagraphStyle('Tech', parent=body_style, leftIndent=8*font_scale)))
                    
                for bullet in job.get("bullets", []):
                    cleaned = clean_bullet(bullet)
                    story.append(Paragraph(f"o&nbsp;&nbsp;{cleaned}", bullet_style))
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
                
                left_text = f"<b>{title}</b>" + (f" | Link: {link}" if link else "")
                left_p = Paragraph(left_text, body_style)
                right_p = Paragraph(f"<b>{date}</b>", ParagraphStyle('ProjDateRight', parent=body_style, alignment=2))
                
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
                    story.append(Paragraph(f"<b>Technologies:</b> {tools}", ParagraphStyle('Tools', parent=body_style, leftIndent=8*font_scale)))
                    
                for bullet in proj.get("bullets", []):
                    cleaned = clean_bullet(bullet)
                    story.append(Paragraph(f"o&nbsp;&nbsp;{cleaned}", bullet_style))
                story.append(scale_spacer(1, 3))
            story.append(scale_spacer(1, 2))

        # --- TECHNICAL SKILLS ---
        technical_skills = data.get("technical_skills", {})
        if technical_skills:
            add_section_header("Technical Skills")
            for skill_name, skill_val in technical_skills.items():
                p_text = f"<b>{skill_name}:</b> {skill_val}"
                story.append(Paragraph(p_text, ParagraphStyle('SkillList', parent=body_style, leftIndent=8*font_scale, spaceAfter=2*font_scale)))
            story.append(scale_spacer(1, 4))
            
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
                story.append(Paragraph(f"o&nbsp;&nbsp;{cleaned}", bullet_style))
            for achievement in achievements:
                cleaned = clean_bullet(achievement)
                story.append(Paragraph(f"o&nbsp;&nbsp;{cleaned}", bullet_style))
            story.append(scale_spacer(1, 4))

        # --- EDUCATION ---
        education = data.get("education", [])
        if education:
            add_section_header("Education")
            for edu in education:
                deg = edu.get("degree", "")
                inst = edu.get("institution", "")
                det = edu.get("details", "")
                per = edu.get("period", "")
                
                left_text = f"<b>{deg}</b> &mdash; {inst}"
                left_p = Paragraph(left_text, body_style)
                right_p = Paragraph(f"<b>{per}</b>", ParagraphStyle('EduDateRight', parent=body_style, alignment=2))
                
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
                    story.append(Paragraph(det, ParagraphStyle('EduDet', parent=body_style, leftIndent=8*font_scale)))
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
                right_p = Paragraph(f"<b>{period}</b>", ParagraphStyle('PorDateRight', parent=body_style, alignment=2))
                
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
                    story.append(Paragraph(f"o&nbsp;&nbsp;{cleaned}", bullet_style))
                story.append(scale_spacer(1, 3))
                
        try:
            doc.build(story)
        except Exception as e:
            return False, str(e)
            
        return True, None
