import os
import json
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from resume_builder.templates.base import BaseTemplate

class ExtractedLayoutTemplate(BaseTemplate):
    """
    Universal layout renderer that translates styling parameters from a layout.json 
    config file directly into a ReportLab flowable pipeline.
    """
    def generate(self, data, pdf_filename, accent_color, font_scale, margin_size, spacing_scale=1.0, padding_scale=1.0, **kwargs):
        # Determine current template package path to load its layout configuration
        import sys
        mod = sys.modules[self.__class__.__module__]
        dir_path = os.path.dirname(mod.__file__)
        layout_path = os.path.join(dir_path, "layout.json")
        
        # Default style settings (B&W Left-aligned layout)
        layout = {
            "margins": {"top": 20, "bottom": 20, "left": 36, "right": 36},
            "header": {"alignment": 0, "name_font_size": 18.0, "contact_font_size": 8.5},
            "sections": {"title_font_size": 10.0, "border_below": True, "border_above": False, "border_color": "#000000"},
            "body": {"font_size": 8.0, "leading": 10.5, "bullet_indent": 15}
        }
        
        if os.path.exists(layout_path):
            try:
                with open(layout_path, "r", encoding="utf-8") as f:
                    # Merge uploaded layout configurations
                    loaded_layout = json.load(f)
                    for k in layout.keys():
                        if k in loaded_layout:
                            if isinstance(layout[k], dict) and isinstance(loaded_layout[k], dict):
                                layout[k].update(loaded_layout[k])
                            else:
                                layout[k] = loaded_layout[k]
            except Exception:
                pass
                
        # Helper to scale heights
        def scale_spacer(w, h):
            return Spacer(w, h * font_scale * spacing_scale)
            
        # Enforce Layout Lock overrides
        layout_locked = kwargs.get("layout_locked", False)
        if layout_locked:
            font_scale = 1.0
            spacing_scale = 1.0
            padding_scale = 1.0
            
            m_cfg = layout.get("margins", {})
            top_margin = m_cfg.get("top", 20.0)
            bottom_margin = m_cfg.get("bottom", 20.0)
            left_margin = m_cfg.get("left", 36.0)
            right_margin = m_cfg.get("right", 36.0)
        else:
            # Determine margins from layout or slide settings
            top_margin = max(12, min(32, margin_size))
            bottom_margin = top_margin
            left_margin = max(12, min(54, margin_size * 1.5))
            right_margin = left_margin
            
        doc = SimpleDocTemplate(
            pdf_filename,
            pagesize=letter,
            leftMargin=left_margin,
            rightMargin=right_margin,
            topMargin=top_margin,
            bottomMargin=bottom_margin
        )
        
        width = 612 - (left_margin + right_margin)
        styles = getSampleStyleSheet()
        
        # Load style variables
        head_cfg = layout.get("header", {})
        sec_cfg = layout.get("sections", {})
        body_cfg = layout.get("body", {})
        
        primary_color = colors.HexColor('#000000')
        
        # Determine theme color
        border_color_val = sec_cfg.get("border_color", "#2563EB")
        theme_color = border_color_val if layout_locked else (accent_color if accent_color else border_color_val)
        accent_color_hex = colors.HexColor(theme_color)
        
        name_style = ParagraphStyle(
            'ExtName',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=head_cfg.get("name_font_size", 18.0) * font_scale,
            leading=(head_cfg.get("name_font_size", 18.0) + 3.0) * font_scale,
            textColor=primary_color,
            alignment=head_cfg.get("alignment", 0) # 0 = Left, 1 = Center, 2 = Right
        )
        
        contact_style = ParagraphStyle(
            'ExtContact',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=head_cfg.get("contact_font_size", 8.5) * font_scale,
            leading=(head_cfg.get("contact_font_size", 8.5) + 2.5) * font_scale,
            textColor=primary_color,
            alignment=head_cfg.get("alignment", 0)
        )
        
        section_title_style = ParagraphStyle(
            'ExtSectionTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=sec_cfg.get("title_font_size", 10.0) * font_scale,
            leading=(sec_cfg.get("title_font_size", 10.0) + 2.5) * font_scale,
            textColor=primary_color,
            spaceAfter=2 * font_scale * padding_scale
        )
        
        body_style = ParagraphStyle(
            'ExtBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=body_cfg.get("font_size", 8.0) * font_scale,
            leading=body_cfg.get("leading", 10.5) * font_scale,
            textColor=primary_color
        )
        
        bold_body_style = ParagraphStyle(
            'ExtBoldBody',
            parent=body_style,
            fontName='Helvetica-Bold'
        )
        
        bullet_style = ParagraphStyle(
            'ExtBullet',
            parent=body_style,
            leftIndent=body_cfg.get("bullet_indent", 15) * font_scale,
            firstLineIndent=-10 * font_scale,
            spaceAfter=1 * font_scale * padding_scale
        )
        
        story = []
        
        # --- HEADER ---
        personal = data.get("personal", {})
        name = personal.get("name", "").upper()
        story.append(Paragraph(name, name_style))
        story.append(scale_spacer(1, 2))
        
        # Extract contact block details
        loc = personal.get("location", "")
        phone = personal.get("phone", "")
        email = personal.get("email", "")
        linkedin = personal.get("linkedin", {}).get("display", "")
        github = personal.get("github", {}).get("display", "")
        
        contacts = []
        if loc: contacts.append(loc)
        if phone: contacts.append(phone)
        if email: contacts.append(email)
        if linkedin: contacts.append(linkedin)
        if github: contacts.append(github)
        
        contact_text = " &nbsp;|&nbsp; ".join(contacts)
        story.append(Paragraph(contact_text, contact_style))
        story.append(scale_spacer(1, 4))
        
        # --- HELPER FUNCTIONS ---
        def add_section_header(title):
            p = Paragraph(title.upper(), section_title_style)
            t = Table([[p]], colWidths=[width])
            
            line_above = 0.5 if sec_cfg.get("border_above", False) else 0
            line_below = 0.5 if sec_cfg.get("border_below", True) else 0
            
            t_style = [
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 1),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ]
            if line_above > 0:
                t_style.append(('LINEABOVE', (0,0), (-1,-1), line_above, accent_color_hex))
            if line_below > 0:
                t_style.append(('LINEBELOW', (0,0), (-1,-1), line_below, accent_color_hex))
                
            t.setStyle(TableStyle(t_style))
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
            add_section_header("Experience")
            for job in experience:
                role = job.get("role", "")
                company = job.get("company", "")
                location = job.get("location", "")
                period = job.get("period", "")
                
                left_text = f"<b>{role}</b> &mdash; {company}" + (f" ({location})" if location else "")
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
                
                left_text = f"<b>{title}</b>" + (f" | <a href='{link}'><font color='{accent_color}'>Link</font></a>" if link else "")
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
                    story.append(Paragraph(f"<b>Tools:</b> {tools}", ParagraphStyle('Tools', parent=body_style, leftIndent=8*font_scale)))
                    
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
                p_text = f"<b>{skill_name}:</b> {skill_val}"
                story.append(Paragraph(p_text, ParagraphStyle('SkillList', parent=body_style, leftIndent=8*font_scale, spaceAfter=2*font_scale)))
            story.append(scale_spacer(1, 4))
            
        # --- ACHIEVEMENTS ---
        achievements = data.get("achievements", [])
        if achievements:
            add_section_header("Achievements")
            for achievement in achievements:
                cleaned = clean_bullet(achievement)
                story.append(Paragraph(f"&bull;&nbsp;&nbsp;{cleaned}", bullet_style))
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
                    story.append(Paragraph(f"&bull;&nbsp;&nbsp;{cleaned}", bullet_style))
                story.append(scale_spacer(1, 3))
                
        try:
            doc.build(story)
        except Exception as e:
            return False, str(e)
            
        return True, None
