import os
import json
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_pdf(data=None, pdf_filename="Sejal_Bhagat_Resume.pdf"):
    # Load resume data from JSON file if not provided
    if data is None:
        try:
            with open("resume.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            msg = f"Failed to load resume.json: {e}"
            print(f"\n[ERROR] {msg}")
            print("Please make sure resume.json exists and is valid JSON.\n")
            return False, msg
    
    # 0.28 in top/bottom margins, 0.5 in left/right margins to guarantee single-page fit
    top_bottom_margin = 20
    left_right_margin = 36
    
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        leftMargin=left_right_margin,
        rightMargin=left_right_margin,
        topMargin=top_bottom_margin,
        bottomMargin=top_bottom_margin
    )
    
    # Total printable width = 612 - 72 = 540 points
    width = 540
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom styles (using pure black text and Helvetica as standard)
    name_style = ParagraphStyle(
        'NameStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=23,
        textColor=colors.HexColor('#000000'), # Pure Black
        alignment=1 # Centered
    )
    
    # Contact Info Style
    contact_style = ParagraphStyle(
        'ContactStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.0,
        leading=12.0,
        textColor=colors.HexColor('#000000'), # Pure Black
        alignment=0 # Left aligned
    )
    
    # Section Title Style (Heading 12pt bold capitalized)
    section_title_style = ParagraphStyle(
        'SectionTitleStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=12.5,
        textColor=colors.HexColor('#000000'), # Pure Black
        spaceAfter=0
    )
    
    # Body Text Style
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.2,
        leading=10.5,
        textColor=colors.HexColor('#000000') # Pure Black
    )
    
    # Indented Tech Line Style (italicized)
    tech_style = ParagraphStyle(
        'TechStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.2,
        leading=10.5,
        textColor=colors.HexColor('#000000'),
        leftIndent=12,
        spaceAfter=1
    )
    
    # Indented Bullet Style (with hanging indent)
    bullet_style = ParagraphStyle(
        'BulletStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.2,
        leading=10.5,
        textColor=colors.HexColor('#000000'),
        leftIndent=22,
        firstLineIndent=-10,
        spaceAfter=1
    )
    
    # Skills Bullet Style
    skills_bullet_style = ParagraphStyle(
        'SkillsBulletStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.2,
        leading=10.5,
        textColor=colors.HexColor('#000000'),
        leftIndent=12,
        firstLineIndent=-10,
        spaceAfter=1.5
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
    story.append(Spacer(1, 2))
    
    # Two-column contact table exactly matching the layout in the image
    loc = personal.get("location", "")
    phone = personal.get("phone", "")
    left_p1_text = f"{loc}" + (f" &nbsp;|&nbsp; {phone}" if phone else "")
    left_p1 = Paragraph(left_p1_text, contact_style)
    
    email = personal.get("email", "")
    email_text = f"<a href='mailto:{email}' color='#2563EB'>{email}</a>" if email else ""
    left_p2 = Paragraph(email_text, contact_style)
    
    right_align_style = ParagraphStyle('RightAlignContact', parent=contact_style, alignment=2)
    
    linkedin = personal.get("linkedin", {})
    linkedin_url = linkedin.get("url", "")
    linkedin_display = linkedin.get("display", "")
    linkedin_text = f"<a href='{linkedin_url}' color='#2563EB'>{linkedin_display}</a>" if linkedin_url else ""
    right_p1 = Paragraph(linkedin_text, right_align_style)
    
    github = personal.get("github", {})
    github_url = github.get("url", "")
    github_display = github.get("display", "")
    github_text = f"<a href='{github_url}' color='#2563EB'>{github_display}</a>" if github_url else ""
    right_p2 = Paragraph(github_text, right_align_style)
    
    contact_table = Table([[ [left_p1, left_p2], [right_p1, right_p2] ]], colWidths=[270, 270])
    contact_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(contact_table)
    story.append(Spacer(1, 2))
    
    # --- HELPER FUNCTIONS ---
    def add_section_header(title):
        p = Paragraph(title.upper(), section_title_style)
        t = Table([[p]], colWidths=[width])
        t.setStyle(TableStyle([
            ('LINEABOVE', (0,0), (-1,-1), 0.75, colors.HexColor('#000000')), # Solid black separator line above
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(t)
        story.append(Spacer(1, 2))
        
    def add_row_with_bullet(left_text, right_text, is_bold=True):
        left_p = Paragraph(f"&bull;&nbsp;&nbsp;{left_text}", bold_style if is_bold else body_style)
        
        right_align_style = ParagraphStyle(
            'RightAlignRow',
            parent=body_style,
            fontName='Helvetica-Bold' if is_bold else 'Helvetica',
            alignment=2 # Right aligned
        )
        right_p = Paragraph(right_text, right_align_style)
        
        t = Table([[left_p, right_p]], colWidths=[395, 145])
        t.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0.5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0.5),
        ]))
        story.append(t)
        story.append(Spacer(1, 1))
        
    # --- SUMMARY SECTION ---
    summary_text = data.get("summary", "")
    if summary_text:
        add_section_header("Summary")
        story.append(Paragraph(summary_text, body_style))
        story.append(Spacer(1, 2))
    
    # --- PROFESSIONAL EXPERIENCE SECTION ---
    experience = data.get("experience", [])
    if experience:
        add_section_header("Professional Experience")
        for job in experience:
            role = job.get("role", "")
            company = job.get("company", "")
            location = job.get("location", "")
            period = job.get("period", "")
            
            left_text = f"<b>{role}, {company}</b>" + (f" &nbsp;|&nbsp; <i>{location}</i>" if location else "")
            add_row_with_bullet(left_text, period)
            
            techs = job.get("technologies", "")
            if techs:
                story.append(Paragraph(f"<b>Technologies:</b> {techs}", tech_style))
            
            for bullet in job.get("bullets", []):
                story.append(Paragraph(f"&bull;&nbsp;&nbsp;{bullet}", bullet_style))
        story.append(Spacer(1, 2))
    
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
                left_text = f"<b>{title}</b> &nbsp;|&nbsp; <a href='{link}' color='#2563EB'>Link</a>"
            else:
                left_text = f"<b>{title}</b>"
                
            add_row_with_bullet(left_text, date)
            
            if tools:
                story.append(Paragraph(f"<b>Tools:</b> {tools}", tech_style))
                
            for bullet in proj.get("bullets", []):
                story.append(Paragraph(f"&bull;&nbsp;&nbsp;{bullet}", bullet_style))
        story.append(Spacer(1, 2))
    
    # --- TECHNICAL SKILLS SECTION ---
    technical_skills = data.get("technical_skills", {})
    if technical_skills:
        add_section_header("Technical Skills")
        for skill_name, skill_val in technical_skills.items():
            p_text = f"&bull;&nbsp;&nbsp;<b>{skill_name}:</b> {skill_val}"
            story.append(Paragraph(p_text, skills_bullet_style))
        story.append(Spacer(1, 2))
        
    # --- ACHIEVEMENTS SECTION ---
    achievements = data.get("achievements", [])
    if achievements:
        add_section_header("Achievements")
        for achievement in achievements:
            story.append(Paragraph(f"&bull;&nbsp;&nbsp;{achievement}", skills_bullet_style))
        story.append(Spacer(1, 2))
        
    # --- EDUCATION SECTION ---
    education = data.get("education", [])
    if education:
        add_section_header("Education")
        
        # B.Tech (First item)
        btech = education[0]
        deg = btech.get("degree", "")
        inst = btech.get("institution", "")
        det = btech.get("details", "")
        
        add_row_with_bullet(f"<b>{deg}</b> &mdash; <i>{inst}</i>", "")
        if det:
            story.append(Paragraph(f"<b>{det}</b>", tech_style))
        story.append(Spacer(1, 1))
        
        # Remaining items
        for edu in education[1:]:
            deg = edu.get("degree", "")
            inst = edu.get("institution", "")
            det = edu.get("details", "")
            per = edu.get("period", "")
            
            parts = []
            if deg: parts.append(f"<b>{deg}</b>")
            if inst: parts.append(f"<i>{inst}</i>")
            if det: parts.append(f"<b>{det}</b>")
            if per: parts.append(f"<b>{per}</b>")
            
            left_text = " &nbsp;|&nbsp; ".join(parts)
            add_row_with_bullet(left_text, "", is_bold=True)
            
        story.append(Spacer(1, 2))
    
    # --- POSITION OF RESPONSIBILITY SECTION ---
    por = data.get("position_of_responsibility", [])
    if por:
        add_section_header("Position of Responsibility")
        for item in por:
            role = item.get("role", "")
            period = item.get("period", "")
            add_row_with_bullet(f"<b>{role}</b>", period)
            
            for bullet in item.get("bullets", []):
                story.append(Paragraph(f"&bull;&nbsp;&nbsp;{bullet}", bullet_style))
        story.append(Spacer(1, 2))
    
    # Bottom separator line
    bottom_line = Table([[""]], colWidths=[width])
    bottom_line.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,-1), 0.75, colors.HexColor('#000000')),
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
        print("\n" + "!" * 70)
        print(f"[ERROR] {msg}")
        print("!" * 70 + "\n")
        return False, msg
    
    print("Resume PDF successfully compiled.")
    
    warning_msg = None
    # Check page count and warn if it exceeds 1 page
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_filename)
        num_pages = len(reader.pages)
        if num_pages > 1:
            warning_msg = f"Resume layout exceeds the target page limit! Current page count: {num_pages} page(s). Please shorten your content to keep it to 1 page."
            print("\n" + "!" * 70)
            print(f"[WARNING] {warning_msg}")
            print("!" * 70 + "\n")
        else:
            print("[SUCCESS] Page count check passed: Exactly 1 page.")
    except Exception as e:
        print(f"[NOTE] Could not check page count programmatically: {e}")
        
    return True, warning_msg

if __name__ == "__main__":
    generate_pdf()
