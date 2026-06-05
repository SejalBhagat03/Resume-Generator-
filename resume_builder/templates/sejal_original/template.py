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
        
        # Margins and width dynamically scaled
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
        
        # Total printable width = 612 - 2 * left_right_margin
        width = 612 - (2 * left_right_margin)
        
        # Styles
        styles = getSampleStyleSheet()
        
        # Custom styles scaled by font_scale
        name_style = ParagraphStyle(
            'NameStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=21 * font_scale,
            leading=24 * font_scale,
            textColor=colors.HexColor('#1E1B4B'), # Elegant Navy
            alignment=1 # Centered
        )
        
        # Section Title Style (Heading 10.5pt bold capitalized)
        section_title_style = ParagraphStyle(
            'SectionTitleStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10.5 * font_scale,
            leading=13.0 * font_scale,
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
            textColor=colors.HexColor('#1E293B') # Slate 800
        )
        
        # Indented Tech Line Style (italicized)
        tech_style = ParagraphStyle(
            'TechStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=8.2 * font_scale,
            leading=10.5 * font_scale,
            textColor=colors.HexColor('#475569'), # Slate 600
            leftIndent=12 * font_scale,
            spaceAfter=1 * font_scale * padding_scale
        )
        
        # Indented Bullet Style (with hanging indent)
        bullet_style = ParagraphStyle(
            'BulletStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.2 * font_scale,
            leading=10.5 * font_scale,
            textColor=colors.HexColor('#1E293B'),
            leftIndent=12 * font_scale,
            firstLineIndent=-10 * font_scale,
            spaceAfter=1 * font_scale * padding_scale
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
        story.append(Paragraph(name, name_style))
        story.append(scale_spacer(1, 2.5))
        
        # Centered Contact Info block
        loc = personal.get("location", "")
        phone = personal.get("phone", "")
        email = personal.get("email", "")
        
        linkedin = personal.get("linkedin", {})
        linkedin_url = linkedin.get("url", "")
        linkedin_display = linkedin.get("display", "")
        
        github = personal.get("github", {})
        github_url = github.get("url", "")
        github_display = github.get("display", "")
        
        contact_parts = []
        if loc:
            contact_parts.append(loc)
        if phone:
            contact_parts.append(phone)
        if email:
            contact_parts.append(f"<a href='mailto:{email}'><font color='{accent_color}'>{email}</font></a>")
            
        linkedin_parts = []
        if linkedin_display and linkedin_url:
            linkedin_parts.append(f"<a href='{linkedin_url}'><font color='{accent_color}'>{linkedin_display}</font></a>")
        github_parts = []
        if github_display and github_url:
            github_parts.append(f"<a href='{github_url}'><font color='{accent_color}'>{github_display}</font></a>")
            
        line1_text = " &nbsp;&bull;&nbsp; ".join(contact_parts)
        socials = linkedin_parts + github_parts
        line2_text = " &nbsp;&bull;&nbsp; ".join(socials)
        
        contact_center_style = ParagraphStyle(
            'ContactCenterStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5 * font_scale,
            leading=11.5 * font_scale,
            textColor=colors.HexColor('#475569'), # Slate 600
            alignment=1 # Centered
        )
        
        if line1_text:
            story.append(Paragraph(line1_text, contact_center_style))
        if line2_text:
            story.append(Paragraph(line2_text, contact_center_style))
            
        story.append(scale_spacer(1, 3.5))
        
        # --- HELPER FUNCTIONS ---
        is_first_section = [True]
        
        def add_section_header(title):
            if not is_first_section[0]:
                story.append(scale_spacer(1, 6)) # Margin before sections for breathing room
            else:
                is_first_section[0] = False
                
            p = Paragraph(title.upper(), section_title_style)
            t = Table([[p]], colWidths=[width])
            t.setStyle(TableStyle([
                ('LINEABOVE', (0,0), (-1,-1), 0.75, colors.HexColor(accent_color)),
                ('TOPPADDING', (0,0), (-1,-1), 3.5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(t)
            story.append(scale_spacer(1, 2.5))
            
        def add_row_header(left_text, right_text, is_bold=True):
            left_p = Paragraph(left_text, bold_style if is_bold else body_style)
            
            right_align_style = ParagraphStyle(
                'RightAlignRow',
                parent=body_style,
                fontName='Helvetica-Bold' if is_bold else 'Helvetica',
                alignment=2 # Right aligned
            )
            right_p = Paragraph(right_text, right_align_style)
            
            t = Table([[left_p, right_p]], colWidths=[width * 0.75, width * 0.25])
            t.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 1.5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
            ]))
            story.append(t)
            story.append(scale_spacer(1, 1))
    
        def clean_bullet(text):
            if not text:
                return ""
            text = text.strip()
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
                
                left_text = f"<b>{role}</b>, {company}" + (f" &nbsp;|&nbsp; <i>{location}</i>" if location else "")
                add_row_header(left_text, period, is_bold=False)
                
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
                    left_text = f"<b>{title}</b> &nbsp;|&nbsp; <a href='{link}'><font color='{accent_color}'>Link</font></a>"
                else:
                    left_text = f"<b>{title}</b>"
                    
                add_row_header(left_text, date, is_bold=False)
                
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
                story.append(Paragraph(p_text, bullet_style))
            story.append(scale_spacer(1, 2))
            
        # --- ACHIEVEMENTS SECTION ---
        achievements = data.get("achievements", [])
        if achievements:
            add_section_header("Achievements")
            for achievement in achievements:
                cleaned = clean_bullet(achievement)
                story.append(Paragraph(f"&bull;&nbsp;&nbsp;{cleaned}", bullet_style))
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
                add_row_header(left_text, per, is_bold=False)
                if det:
                    story.append(Paragraph(det, tech_style))
                story.append(scale_spacer(1, 1))
            story.append(scale_spacer(1, 2))
        
        # --- POSITION OF RESPONSIBILITY SECTION ---
        por = data.get("position_of_responsibility", [])
        if por:
            add_section_header("Position of Responsibility")
            for item in por:
                role = item.get("role", "")
                period = item.get("period", "")
                add_row_header(f"<b>{role}</b>", period, is_bold=False)
                
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
