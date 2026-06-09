import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from resume_builder.templates.base import BaseTemplate

class SejalOriginalTemplate(BaseTemplate):
    def generate(self, data, pdf_filename, accent_color, font_scale, margin_size, spacing_scale=1.0, padding_scale=1.0, **kwargs):
        # Helper to scale spacers dynamically without shadowing the Spacer class
        def scale_spacer(w, h):
            return Spacer(w, h * font_scale * spacing_scale)
        
        # Margins and width dynamically scaled (margins from backup script are 1.8x on sides)
        top_bottom_margin = margin_size
        left_right_margin = margin_size * 1.8
        
        doc = SimpleDocTemplate(
            pdf_filename,
            pagesize=letter,
            leftMargin=left_right_margin,
            rightMargin=left_right_margin,
            topMargin=top_bottom_margin,
            bottomMargin=top_bottom_margin
        )
        
        # Total printable width = 612 - 2 * left_right_margin
        width = 612 - (2 * left_right_margin)
        
        # Styles
        styles = getSampleStyleSheet()
        
        # Custom styles scaled by font_scale (matching backup script exactly)
        name_style = ParagraphStyle(
            'NameStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=20 * font_scale,
            leading=23 * font_scale,
            textColor=colors.HexColor('#000000'), # Pure Black
            alignment=1 # Centered
        )
        
        # Contact Info Style
        contact_style = ParagraphStyle(
            'ContactStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9.0 * font_scale,
            leading=12.0 * font_scale,
            textColor=colors.HexColor('#000000'), # Pure Black
            alignment=0 # Left aligned
        )
        
        # Section Title Style (Heading 10.5pt bold capitalized)
        section_title_style = ParagraphStyle(
            'SectionTitleStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10.5 * font_scale,
            leading=12.5 * font_scale,
            textColor=colors.HexColor('#000000'), # Pure Black
            spaceAfter=0
        )
        
        # Body Text Style
        body_style = ParagraphStyle(
            'BodyStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.2 * font_scale,
            leading=10.5 * font_scale,
            textColor=colors.HexColor('#000000') # Pure Black
        )
        
        # Indented Tech Line Style (italicized)
        tech_style = ParagraphStyle(
            'TechStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=8.2 * font_scale,
            leading=10.5 * font_scale,
            textColor=colors.HexColor('#000000'),
            leftIndent=12 * font_scale,
            spaceAfter=1 * font_scale * padding_scale
        )
        
        # Indented Bullet Style (with hanging indent of 22pt)
        bullet_style = ParagraphStyle(
            'BulletStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.2 * font_scale,
            leading=10.5 * font_scale,
            textColor=colors.HexColor('#000000'),
            leftIndent=22 * font_scale,
            firstLineIndent=-10 * font_scale,
            spaceAfter=1 * font_scale * padding_scale
        )
        
        # Skills Bullet Style (indent of 12pt)
        skills_bullet_style = ParagraphStyle(
            'SkillsBulletStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.2 * font_scale,
            leading=10.5 * font_scale,
            textColor=colors.HexColor('#000000'),
            leftIndent=12 * font_scale,
            firstLineIndent=-10 * font_scale,
            spaceAfter=1.5 * font_scale * padding_scale
        )
        
        # Bold Text Helper
        bold_style = ParagraphStyle(
            'BoldStyle',
            parent=body_style,
            fontName='Helvetica-Bold'
        )
        
        story = []
        
        # --- HEADER SECTION ---
        personal = data.get("personal", {})
        name = personal.get("name", "SEJAL BHAGAT")
        story.append(Paragraph(name.upper(), name_style))
        story.append(scale_spacer(1, 2))
        
        # Professional Title
        title = personal.get("title", "")
        if title:
            title_style = ParagraphStyle(
                'HeaderTitle',
                parent=contact_style,
                fontSize=11 * font_scale,
                leading=13 * font_scale,
                textColor=colors.HexColor(accent_color),
                fontName='Helvetica-Bold'
            )
            story.append(Paragraph(title, title_style))
            story.append(scale_spacer(1, 2))
        
        # Two-column contact table exactly matching the layout in the image
        loc = personal.get("location", "")
        phone = personal.get("phone", "")
        left_p1_text = f"{loc}" + (f" &nbsp;|&nbsp; {phone}" if phone and loc else (phone if phone else ""))
        left_p1 = Paragraph(left_p1_text, contact_style)
        
        email = personal.get("email", "")
        email_text = f"<a href=\"mailto:{email}\"><font color=\"{accent_color}\"><u>{email}</u></font></a>" if email else ""
        left_p2 = Paragraph(email_text, contact_style)
        
        right_align_style = ParagraphStyle('RightAlignContact', parent=contact_style, alignment=2)
        
        linkedin = personal.get("linkedin", {})
        linkedin_url = linkedin.get("url", "")
        linkedin_display = linkedin.get("display", "")
        linkedin_text = f"<a href=\"{linkedin_url}\"><font color=\"{accent_color}\"><u>{linkedin_display}</u></font></a>" if linkedin_url else ""
        right_p1 = Paragraph(linkedin_text, right_align_style)
        
        github = personal.get("github", {})
        github_url = github.get("url", "")
        github_display = github.get("display", "")
        github_text = f"<a href=\"{github_url}\"><font color=\"{accent_color}\"><u>{github_display}</u></font></a>" if github_url else ""
        right_p2 = Paragraph(github_text, right_align_style)
        
        contact_table = Table([[ [left_p1, left_p2], [right_p1, right_p2] ]], colWidths=[width/2.0, width/2.0])
        contact_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(contact_table)
        story.append(scale_spacer(1, 2))
        
        # --- HELPER FUNCTIONS ---
        def add_section_header(title):
            p = Paragraph(title.upper(), section_title_style)
            t = Table([[p]], colWidths=[width])
            t.setStyle(TableStyle([
                ('LINEABOVE', (0,0), (-1,-1), 0.75, colors.HexColor(accent_color)), # Accent separator line above
                ('TOPPADDING', (0,0), (-1,-1), 3),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(t)
            story.append(scale_spacer(1, 2))
            
        def add_row_with_bullet(left_text, right_text, is_bold=True):
            left_p = Paragraph(f"&bull;&nbsp;&nbsp;{left_text}", bold_style if is_bold else body_style)
            
            right_align_style = ParagraphStyle(
                'RightAlignRow',
                parent=body_style,
                fontName='Helvetica-Bold' if is_bold else 'Helvetica',
                alignment=2 # Right aligned
            )
            right_p = Paragraph(right_text, right_align_style)
            
            t = Table([[left_p, right_p]], colWidths=[width * 0.73, width * 0.27])
            t.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 0.5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0.5),
            ]))
            story.append(t)
            story.append(scale_spacer(1, 1))

        def clean_bullet(text):
            if not text:
                return ""
            text = text.strip()
            # Strip common bullet prefixes
            for prefix in ["&bull;", "•", "-", "*"]:
                if text.startswith(prefix):
                    text = text[len(prefix):].strip()
            return text
            
        # --- SUMMARY SECTION ---
        summary_text = data.get("summary", "")
        if summary_text:
            add_section_header("Summary")
            story.append(Paragraph(summary_text, body_style))
            story.append(scale_spacer(1, 2))
        
        # --- PROFESSIONAL EXPERIENCE SECTION ---
        experience = data.get("experience", [])
        if experience:
            add_section_header("Professional Experience")
            for job in experience:
                role = job.get("role", "")
                company = job.get("company", "")
                location = job.get("location", "")
                period = job.get("period", "")
                
                left_text = f"<b>{role}</b>" + (f", {company}" if company else "") + (f" &nbsp;|&nbsp; <i>{location}</i>" if location else "")
                add_row_with_bullet(left_text, period, is_bold=False)
                
                techs = job.get("technologies", "")
                if techs:
                    story.append(Paragraph(f"<b>Technologies:</b> {techs}", tech_style))
                
                for bullet in job.get("bullets", []):
                    cleaned = clean_bullet(bullet)
                    story.append(Paragraph(f"&bull;&nbsp;&nbsp;{cleaned}", bullet_style))
            story.append(scale_spacer(1, 2))
        
        # --- PROJECTS SECTION ---
        projects = data.get("projects", [])
        if projects:
            add_section_header("Projects")
            for proj in projects:
                title = proj.get("title", "")
                link = proj.get("link", "")
                date = proj.get("date", "")
                tools = proj.get("tools", "")
                
                if link:
                    left_text = f"<b>{title}</b> &nbsp;|&nbsp; <a href=\"{link}\"><font color=\"{accent_color}\"><u>Link</u></font></a>"
                else:
                    left_text = f"<b>{title}</b>"
                    
                add_row_with_bullet(left_text, date, is_bold=False)
                
                if tools:
                    story.append(Paragraph(f"<b>Tools:</b> {tools}", tech_style))
                    
                for bullet in proj.get("bullets", []):
                    cleaned = clean_bullet(bullet)
                    story.append(Paragraph(f"&bull;&nbsp;&nbsp;{cleaned}", bullet_style))
            story.append(scale_spacer(1, 2))
        
        # --- TECHNICAL SKILLS SECTION ---
        technical_skills = data.get("technical_skills", {})
        if technical_skills:
            add_section_header("Technical Skills")
            for skill_name, skill_val in technical_skills.items():
                p_text = f"&bull;&nbsp;&nbsp;<b>{skill_name}:</b> {skill_val}"
                story.append(Paragraph(p_text, skills_bullet_style))
            story.append(scale_spacer(1, 2))
            
        # --- CERTIFICATIONS & ACHIEVEMENTS SECTION ---
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
                story.append(Paragraph(f"&bull;&nbsp;&nbsp;{cleaned}", skills_bullet_style))
            for achievement in achievements:
                cleaned = clean_bullet(achievement)
                story.append(Paragraph(f"&bull;&nbsp;&nbsp;{cleaned}", skills_bullet_style))
            story.append(scale_spacer(1, 2))
            
        # --- EDUCATION SECTION ---
        education = data.get("education", [])
        if education:
            add_section_header("Education")
            for edu in education:
                deg = edu.get("degree", "")
                inst = edu.get("institution", "")
                det = edu.get("details", "")
                per = edu.get("period", "")
                
                left_text = f"<b>{deg}</b>" + (f" &nbsp;|&nbsp; <i>{inst}</i>" if inst else "")
                
                # If the period is long (e.g., "Expected Graduation: 2026"), it is cleaner to put it
                # on the second line alongside the CGPA details, matching Sejal's original layout.
                is_period_long = len(per) > 9 or "expect" in per.lower() or "grad" in per.lower()
                
                if is_period_long:
                    add_row_with_bullet(left_text, "", is_bold=False)
                    second_line_parts = []
                    if det:
                        second_line_parts.append(det)
                    if per:
                        second_line_parts.append(per)
                    if second_line_parts:
                        det_text = " &nbsp;|&nbsp; ".join(second_line_parts)
                        story.append(Paragraph(det_text, tech_style))
                else:
                    # For short periods (like 12th/10th), place both Grade and Period on the same line to save vertical space
                    right_parts = []
                    if det:
                        right_parts.append(det)
                    if per:
                        right_parts.append(per)
                    right_text = " &nbsp;|&nbsp; ".join(right_parts)
                    add_row_with_bullet(left_text, right_text, is_bold=False)
                
                story.append(scale_spacer(1, 1))
            story.append(scale_spacer(1, 2))
        
        # --- POSITION OF RESPONSIBILITY SECTION ---
        por = data.get("position_of_responsibility", [])
        if por:
            add_section_header("Position of Responsibility")
            for item in por:
                role = item.get("role", "")
                period = item.get("period", "")
                add_row_with_bullet(f"<b>{role}</b>", period, is_bold=False)
                
                for bullet in item.get("bullets", []):
                    cleaned = clean_bullet(bullet)
                    story.append(Paragraph(f"&bull;&nbsp;&nbsp;{cleaned}", bullet_style))
            story.append(scale_spacer(1, 2))

        # Bottom separator line
        bottom_line = Table([[""]], colWidths=[width])
        bottom_line.setStyle(TableStyle([
            ('LINEABOVE', (0,0), (-1,-1), 0.75, colors.HexColor(accent_color)),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(bottom_line)
        
        # Build Document
        try:
            doc.build(story)
        except (PermissionError, OSError) as e:
            msg = f"Could not write to '{pdf_filename}'! Please make sure the PDF file is NOT currently open in Adobe Reader, Chrome, or another viewer. Error: {e}"
            return False, msg
        
        warning_msg = None
        # Check page count and warn if it exceeds 1 page
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_filename)
            num_pages = len(reader.pages)
            if num_pages > 1:
                warning_msg = f"Resume layout exceeds the target page limit! Current page count: {num_pages} page(s). Please shorten your content to keep it to 1 page."
        except Exception as e:
            # Silent fallback if pypdf reader fails
            pass
            
        return True, warning_msg
