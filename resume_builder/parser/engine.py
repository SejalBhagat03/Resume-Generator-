import re
import json

def parse_contact_details(text):
    """
    Heuristically extracts contact info from text block using regex.
    """
    contacts = {
        "name": "",
        "email": "",
        "phone": "",
        "location": "",
        "linkedin": {"display": "", "url": ""},
        "github": {"display": "", "url": ""}
    }
    
    # 1. Email Regex
    email_match = re.search(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', text)
    if email_match:
        contacts["email"] = email_match.group(1).strip()
        
    # 2. Phone Regex (supports international, brackets, spaces, hyphens)
    phone_match = re.search(r'((?:\+\d{1,3}[-\s]?)?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}|\+91\s*\d{10}|\b\d{10}\b)', text)
    if phone_match:
        contacts["phone"] = phone_match.group(1).strip()
        
    # 3. LinkedIn URL — handle linkedin.com/in/User AND linkedin/User.Name shorthand
    li_match = re.search(
        r'linkedin\.com/in/([a-zA-Z0-9_.\-]+)|linkedin\.com/([a-zA-Z0-9_.\-]+)|linkedin/([a-zA-Z0-9_.\-]+)',
        text, re.IGNORECASE
    )
    if li_match:
        # Grab whichever capture group matched
        username = next(g for g in li_match.groups() if g)
        full_url = f"https://linkedin.com/in/{username}"
        contacts["linkedin"] = {
            "display": f"linkedin.com/in/{username}",
            "url": full_url
        }
        
    # 4. GitHub URL — handle github.com/User AND github/User shorthand
    gh_match = re.search(
        r'github\.com/([a-zA-Z0-9_.\-]+)|github/([a-zA-Z0-9_.\-]+)',
        text, re.IGNORECASE
    )
    if gh_match:
        username = next(g for g in gh_match.groups() if g)
        full_url = f"https://github.com/{username}"
        contacts["github"] = {
            "display": f"github.com/{username}",
            "url": full_url
        }
        
    # 5. Location (City, Country / State)
    loc_match = re.search(r'\b([A-Z][a-zA-Z\s]+,\s*[A-Z][a-zA-Z\s]+)\b', text)
    if loc_match:
        # Ignore common keywords that might match the pattern
        potential = loc_match.group(1).strip()
        if not any(k in potential.lower() for k in ["linkedin", "github", "email", "phone"]):
            contacts["location"] = potential
            
    # 6. Name Heuristics: Usually the first line of the document that is not empty
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for line in lines[:5]:
        # Filter out lines with links, email, phone, or url-like characters
        if "@" in line or "http" in line or "+" in line:
            continue
        # Allow dots in names (e.g. "Dr. Smith") but skip lines with multiple slashes (URLs)
        if line.count("/") > 1:
            continue
        words = line.split()
        if 2 <= len(words) <= 4:
            contacts["name"] = line
            break
            
    if not contacts["name"] and lines:
        contacts["name"] = lines[0]
        
    return contacts

def segment_sections(text):
    """
    Splits resume text into sections based on header keywords.
    """
    section_keywords = {
        "summary": ["summary", "profile", "professional summary", "objective", "career objective", "about me"],
        "experience": ["experience", "professional experience", "work experience", "employment history", "work history", "internships"],
        "projects": ["projects", "academic projects", "personal projects", "key projects"],
        "skills": ["skills", "technical skills", "core competencies", "skills & competencies", "expertise", "languages"],
        "education": ["education", "academic qualifications", "academic background", "education history", "qualifications"],
        "achievements": ["achievements", "accomplishments", "awards", "honors", "publications"],
        "position_of_responsibility": ["position of responsibility", "positions of responsibility", "leadership", "extracurricular", "volunteering"]
    }
    
    lines = text.split("\n")
    current_section = "personal" # Header section before any keyword
    buffers = {k: [] for k in section_keywords.keys()}
    buffers["personal"] = []
    
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        # Check if line matches a section header
        found_header = False
        # Strip bullets or extra chars to verify header text
        h_text = re.sub(r'^[\W\d_]+', '', line_clean).strip().lower()
        
        for sec_id, keywords in section_keywords.items():
            if h_text in keywords or (len(h_text) < 30 and any(h_text == kw for kw in keywords)):
                current_section = sec_id
                found_header = True
                break
                
        if not found_header:
            buffers[current_section].append(line_clean)
            
    return buffers

def parse_experience(lines):
    """
    Parses segment buffer into structured list of jobs.
    """
    jobs = []
    current_job = None
    
    # Date match pattern (e.g. Dec 2023 - Present, 2024, 05/2022-06/2023)
    date_pattern = re.compile(
        r'(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s*\d{4}\s*[-–—to\s]+\s*(?:Present|Current|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December|\d{4})|\b\d{4}\s*[-–—to\s]+\s*(?:\d{4}|Present)|\b\d{2}/\d{4}\s*[-–—\s]+\s*(?:\d{2}/\d{4}|Present))',
        re.IGNORECASE
    )
    
    for line in lines:
        is_bullet = line.startswith(('•', '-', '*', 'o', '▪', 'v', 'bullet')) or re.match(r'^\d+[\.\)]', line)
        cleaned_line = re.sub(r'^[\W\d_]+', '', line).strip()
        
        # If it contains dates and is NOT a bullet, it's likely a job entry header
        date_match = date_pattern.search(line)
        if date_match and not is_bullet:
            if current_job:
                jobs.append(current_job)
                
            period = date_match.group(1).strip()
            # Remove date from header line to parse role and company
            header_text = date_pattern.sub("", line).strip()
            
            # Split role/company by separators
            parts = [p.strip() for p in re.split(r'[|—–\-•,]', header_text) if p.strip()]
            role = parts[0] if len(parts) > 0 else "Software Engineer"
            company = parts[1] if len(parts) > 1 else ""
            location = parts[2] if len(parts) > 2 else ""
            
            current_job = {
                "role": role,
                "company": company,
                "location": location,
                "period": period,
                "technologies": "",
                "bullets": []
            }
        else:
            if not current_job:
                current_job = {
                    "role": "Software Engineer",
                    "company": "Company",
                    "location": "",
                    "period": "",
                    "technologies": "",
                    "bullets": []
                }
                
            if is_bullet:
                current_job["bullets"].append(cleaned_line)
            else:
                # Check for Tech stack listing in experience
                if "technologies:" in line.lower() or "tech:" in line.lower() or "tools:" in line.lower():
                    tech_part = re.sub(r'^(technologies|tech|tools)\s*:\s*', '', line, flags=re.IGNORECASE).strip()
                    current_job["technologies"] = tech_part
                else:
                    # Append description text to bullets
                    current_job["bullets"].append(line)
                    
    if current_job:
        jobs.append(current_job)
    return jobs

def parse_projects(lines):
    """
    Parses segment buffer into structured list of projects.
    """
    projects = []
    current_proj = None
    
    # Matches full URLs or bare github.com paths
    url_pattern = re.compile(r'https?://[^\s]+', re.IGNORECASE)
    gh_bare_pattern = re.compile(r'github\.com/[^\s|,]+', re.IGNORECASE)
    date_pattern = re.compile(
        r'(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|'
        r'May|June|July|August|September|October|November|December)\s*\d{4}|\b\d{4})',
        re.IGNORECASE
    )
    
    for line in lines:
        is_bullet = line.startswith(('•', '-', '*', 'o', '▪')) or re.match(r'^\d+[\.\)]', line)
        cleaned_line = re.sub(r'^[\W\d_]+', '', line).strip()
        
        # Extract URL from line: prefer full URL, fall back to bare github.com path
        url_match = url_pattern.search(line)
        gh_match = gh_bare_pattern.search(line)
        if url_match:
            link = url_match.group(0).strip("()[]{},")
        elif gh_match:
            link = "https://" + gh_match.group(0).strip("()[]{},")
        else:
            link = ""
        
        # Detect '| GitHub' or '| Link' as a clickable cue (even without a URL)
        has_github_label = bool(re.search(r'\|\s*github\b', line, re.IGNORECASE))
        
        date_match = date_pattern.search(line)
        date = date_match.group(1).strip() if date_match else ""
        
        # Determine if this line is a new project header:
        # - Not a bullet point
        # - Has a date, OR a URL, OR a '| GitHub' label, OR is short enough to be a title
        is_header = (not is_bullet) and (link or has_github_label or date_match or 
                                          (len(line) < 80 and not current_proj))
        
        if is_header:
            if current_proj:
                projects.append(current_proj)
                
            # Extract title: take the text before the first pipe '|', strip date and URL
            # Split on pipe first to get the project name cleanly
            pipe_parts = line.split('|')
            title_raw = pipe_parts[0]  # Everything before the first pipe
            title_raw = date_pattern.sub("", title_raw)   # remove date
            title_raw = url_pattern.sub("", title_raw)    # remove full URLs
            title_raw = gh_bare_pattern.sub("", title_raw) # remove bare github paths
            # Clean up separators and whitespace
            title_raw = re.sub(r'[\-—–\(\)]+', '', title_raw).strip()
            # Collapse multiple spaces
            title_raw = re.sub(r'\s{2,}', ' ', title_raw).strip()
            
            # If title is still empty, check remainder of pipe parts
            if not title_raw and len(pipe_parts) > 1:
                for part in pipe_parts[1:]:
                    candidate = re.sub(r'(?i)github|link|gitlab', '', part).strip()
                    candidate = re.sub(r'[^a-zA-Z0-9\s]', '', candidate).strip()
                    if candidate:
                        title_raw = candidate
                        break
            
            # Build project link: if we found a GitHub label but no URL,
            # try to construct one from the full line's github mention
            if not link and has_github_label:
                # Try to find username from a github.com reference earlier in the doc
                # but for now just leave link empty (better than a wrong URL)
                link = ""
            
            current_proj = {
                "title": title_raw if title_raw else "Untitled Project",
                "link": link,
                "date": date,
                "tools": "",
                "bullets": []
            }
        else:
            if not current_proj:
                current_proj = {
                    "title": "Untitled Project",
                    "link": "",
                    "date": "",
                    "tools": "",
                    "bullets": []
                }
                
            if is_bullet:
                current_proj["bullets"].append(cleaned_line)
            else:
                if re.match(r'^(tools|tech|technologies)\s*:', line, re.IGNORECASE):
                    tools_part = re.sub(r'^(tools|tech|technologies)\s*:\s*', '', line,
                                        flags=re.IGNORECASE).strip()
                    current_proj["tools"] = tools_part
                else:
                    current_proj["bullets"].append(line)
                    
    if current_proj:
        projects.append(current_proj)
    return projects

def parse_skills(lines):
    """
    Parses segment buffer into structured skills dictionary (Category -> List).
    """
    skills = {}
    
    for line in lines:
        if ":" in line:
            parts = line.split(":", 1)
            cat = parts[0].strip()
            val = parts[1].strip()
            skills[cat] = val
        else:
            # Fallback when there is just a list of skills
            vals = [v.strip() for v in line.split(",") if v.strip()]
            if vals:
                # Add to a general category
                existing = skills.get("Technical Skills", "")
                skills["Technical Skills"] = (existing + ", " if existing else "") + ", ".join(vals)
                
    return skills

def parse_education(lines):
    """
    Parses segment buffer into structured education blocks.
    """
    edu_list = []
    current_edu = None
    
    degree_kw = ["b.tech", "m.tech", "b.s", "m.s", "phd", "bachelor", "master", "high school", "ssc", "hsc", "cbse", "degree", "b.e", "b.c.a", "m.c.a"]
    date_pattern = re.compile(r'(\b\d{4}\s*[-–—to\s]+\s*\d{4}|\b\d{4})')
    
    for line in lines:
        is_bullet = line.startswith(('•', '-', '*', 'o'))
        
        date_match = date_pattern.search(line)
        has_degree_kw = any(dkw in line.lower() for dkw in degree_kw)
        
        if not is_bullet and (has_degree_kw or date_match or not current_edu):
            if current_edu:
                edu_list.append(current_edu)
                
            period = date_match.group(1).strip() if date_match else ""
            rest_text = date_pattern.sub("", line).strip()
            
            parts = [p.strip() for p in re.split(r'[|—–\-•,]', rest_text) if p.strip()]
            degree = parts[0] if len(parts) > 0 else "Degree / Major"
            inst = parts[1] if len(parts) > 1 else ""
            
            current_edu = {
                "degree": degree,
                "institution": inst,
                "details": "",
                "period": period
            }
        else:
            if not current_edu:
                current_edu = {
                    "degree": "Degree / Major",
                    "institution": "",
                    "details": "",
                    "period": ""
                }
                
            # Grade or CGPA pattern matching
            gpa_match = re.search(r'((?:CGPA|GPA|Grade)\s*:\s*\d+(?:\.\d+)?(?:\s*/\s*\d+)?|\b\d{2}\.?\d?%)', line, re.IGNORECASE)
            if gpa_match:
                current_edu["details"] = gpa_match.group(1).strip()
            else:
                # Accumulate details
                current_edu["details"] = (current_edu["details"] + " " if current_edu["details"] else "") + line.strip()
                
    if current_edu:
        edu_list.append(current_edu)
    return edu_list

def parse_por(lines):
    """
    Parses Position of Responsibility segment buffer.
    """
    pors = []
    current_por = None
    
    date_pattern = re.compile(r'(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)?\s*\d{4}\s*[-–—to\s]+\s*(?:Present|Current|\d{4})|\b\d{4})', re.IGNORECASE)
    
    for line in lines:
        is_bullet = line.startswith(('•', '-', '*', 'o'))
        cleaned_line = re.sub(r'^[\W\d_]+', '', line).strip()
        
        date_match = date_pattern.search(line)
        if not is_bullet and (date_match or not current_por):
            if current_por:
                pors.append(current_por)
                
            period = date_match.group(1).strip() if date_match else ""
            role_text = date_pattern.sub("", line).strip()
            role_text = re.sub(r'[|,\-—–\(\)]', '', role_text).strip()
            
            current_por = {
                "role": role_text if role_text else "Leadership Role",
                "period": period,
                "bullets": []
            }
        else:
            if not current_por:
                current_por = {
                    "role": "Leadership Role",
                    "period": "",
                    "bullets": []
                }
            if is_bullet:
                current_por["bullets"].append(cleaned_line)
            else:
                current_por["bullets"].append(line)
                
    if current_por:
        pors.append(current_por)
    return pors

def parse_extracted_text_to_json(text):
    """
    Splits text into sections and parses each section into JSON resume schema.
    """
    buffers = segment_sections(text)
    
    personal_text = "\n".join(buffers["personal"])
    contacts = parse_contact_details(personal_text)
    
    summary_text = " ".join([l.strip() for l in buffers["summary"] if l.strip()])
    
    experience = parse_experience(buffers["experience"])
    projects = parse_projects(buffers["projects"])
    skills = parse_skills(buffers["skills"])
    education = parse_education(buffers["education"])
    
    # Achievements is a list of strings
    achievements = []
    for line in buffers["achievements"]:
        cleaned = re.sub(r'^[\W\d_]+', '', line).strip()
        if cleaned:
            achievements.append(cleaned)
            
    por = parse_por(buffers["position_of_responsibility"])
    
    return {
        "personal": contacts,
        "summary": summary_text,
        "experience": experience,
        "projects": projects,
        "technical_skills": skills,
        "achievements": achievements,
        "education": education,
        "position_of_responsibility": por
    }

def segment_into_blocks(text):
    """
    Splits text into blocks, where each block starts with a detected header or the start of document.
    Returns list of dicts: {"header": str, "inferred_category": str, "lines": list of str}
    """
    section_keywords = {
        "summary": ["summary", "profile", "professional summary", "objective", "career objective", "about me"],
        "experience": ["experience", "professional experience", "work experience", "employment history", "work history", "internships"],
        "projects": ["projects", "academic projects", "personal projects", "key projects"],
        "skills": ["skills", "technical skills", "core competencies", "skills & competencies", "expertise", "languages"],
        "education": ["education", "academic qualifications", "academic background", "education history", "qualifications"],
        "achievements": ["achievements", "accomplishments", "awards", "honors", "publications"],
        "position_of_responsibility": ["position of responsibility", "positions of responsibility", "leadership", "extracurricular", "volunteering"]
    }
    
    lines = text.split("\n")
    blocks = []
    
    current_header = "Personal Info / Header"
    current_category = "personal"
    current_lines = []
    
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        found_header = False
        h_text = re.sub(r'^[\W\d_]+', '', line_clean).strip().lower()
        
        for sec_id, keywords in section_keywords.items():
            if h_text in keywords or (len(h_text) < 30 and any(h_text == kw for kw in keywords)):
                # Save current block
                if current_lines or current_header != "Personal Info / Header":
                    blocks.append({
                        "header": current_header,
                        "inferred_category": current_category,
                        "lines": current_lines
                    })
                current_header = line_clean
                current_category = sec_id
                current_lines = []
                found_header = True
                break
                
        if not found_header:
            current_lines.append(line_clean)
            
    # Append final block
    if current_lines or current_header != "Personal Info / Header":
        blocks.append({
            "header": current_header,
            "inferred_category": current_category,
            "lines": current_lines
        })
        
    return blocks

def parse_mapped_blocks_to_json(blocks_list):
    """
    Given a list of blocks (each containing 'category' and 'lines'),
    compiles and parses them into the structured resume JSON schema.
    """
    buffers = {
        "personal": [],
        "summary": [],
        "experience": [],
        "projects": [],
        "skills": [],
        "education": [],
        "achievements": [],
        "position_of_responsibility": []
    }
    
    for b in blocks_list:
        cat = b.get("category")
        if cat in buffers:
            buffers[cat].extend(b.get("lines", []))
            
    # Now call the individual structured parsers
    personal_text = "\n".join(buffers["personal"])
    contacts = parse_contact_details(personal_text)
    
    summary_text = " ".join([l.strip() for l in buffers["summary"] if l.strip()])
    
    experience = parse_experience(buffers["experience"])
    projects = parse_projects(buffers["projects"])
    skills = parse_skills(buffers["skills"])
    education = parse_education(buffers["education"])
    
    achievements = []
    for line in buffers["achievements"]:
        cleaned = re.sub(r'^[\W\d_]+', '', line).strip()
        if cleaned:
            achievements.append(cleaned)
            
    por = parse_por(buffers["position_of_responsibility"])
    
    return {
        "personal": contacts,
        "summary": summary_text,
        "experience": experience,
        "projects": projects,
        "technical_skills": skills,
        "achievements": achievements,
        "education": education,
        "position_of_responsibility": por
    }

# ----------------- LAYOUT STYLE EXTRACTOR -----------------
def analyze_style_from_runs(runs_data, margins_pt=None):
    """
    Inspects extracted text-runs to heuristically build a layout.json config.
    """
    layout = {
        "margins": {"top": 20, "bottom": 20, "left": 36, "right": 36},
        "header": {"alignment": 1, "name_font_size": 20, "contact_font_size": 9.0},
        "sections": {"title_font_size": 10.5, "border_below": False, "border_above": True, "border_color": "#2563EB"},
        "body": {"font_size": 8.2, "leading": 10.5, "bullet_indent": 15}
    }
    
    if margins_pt:
        # DOCX margins extracted natively
        layout["margins"] = margins_pt
    else:
        # Estimate margins from PDF runs coordinate boundaries
        x_positions = [run.get("x") for run in runs_data if run.get("x") is not None]
        y_positions = [run.get("y") for run in runs_data if run.get("y") is not None]
        if x_positions and y_positions:
            min_x = min(x_positions)
            max_x = max(x_positions)
            min_y = min(y_positions)
            max_y = max(y_positions)
            
            # Standard letter size page is 612 pt wide, 792 pt tall
            left_m = max(12.0, min(72.0, min_x))
            right_m = max(12.0, min(72.0, 612.0 - max_x))
            top_m = max(12.0, min(72.0, 792.0 - max_y))
            bottom_m = max(12.0, min(72.0, min_y))
            
            layout["margins"] = {
                "top": round(top_m, 1),
                "bottom": round(bottom_m, 1),
                "left": round(left_m, 1),
                "right": round(right_m, 1)
            }
        
    if not runs_data:
        return layout
        
    # 1. Color Extraction (Find the most common colored text hex)
    hex_colors = []
    for run in runs_data:
        color = run.get("color")
        if color and color != "#000000" and color != "#ffffff" and color.startswith("#"):
            # Check length is valid
            if len(color) in [4, 7]:
                hex_colors.append(color.upper())
                
    if hex_colors:
        # Find mode color
        most_common_color = max(set(hex_colors), key=hex_colors.count)
        layout["sections"]["border_color"] = most_common_color
        
    # 2. Font Sizing Analysis
    font_sizes = [run.get("font_size", 10.0) for run in runs_data]
    if font_sizes:
        max_size = max(font_sizes)
        layout["header"]["name_font_size"] = max(16.0, min(26.0, max_size))
        
        # Body text size is typically the median size
        sorted_sizes = sorted(font_sizes)
        median_size = sorted_sizes[len(sorted_sizes) // 2]
        layout["body"]["font_size"] = max(7.5, min(11.0, median_size))
        layout["body"]["leading"] = layout["body"]["font_size"] + 2.5
        
        # Section titles size is between body size and max size
        title_candidates = [s for s in font_sizes if median_size < s < max_size]
        if title_candidates:
            avg_title = sum(title_candidates) / len(title_candidates)
            layout["sections"]["title_font_size"] = max(9.5, min(14.0, avg_title))
        else:
            layout["sections"]["title_font_size"] = layout["body"]["font_size"] + 2.0
            
    # 3. Header Alignment Heuristic (PDF runs coordinate scanning)
    # Check alignment of first 3 runs (usually name + contacts)
    align_votes = []
    for run in runs_data[:3]:
        align = run.get("alignment")
        if align is not None:
            align_votes.append(align)
        elif run.get("x") is not None:
            # standard width is 612. Center is around 250-360 X coord
            x = run.get("x")
            if 180 <= x <= 320:
                align_votes.append(1) # Center
            else:
                align_votes.append(0) # Left
                
    if align_votes:
        layout["header"]["alignment"] = max(set(align_votes), key=align_votes.count)
        
    # 4. Two-Column Layout Detection
    x_positions = [run.get("x") for run in runs_data if run.get("x") is not None]
    if x_positions:
        left_count = sum(1 for x in x_positions if x < 200)
        right_count = sum(1 for x in x_positions if x >= 220)
        total_valid = left_count + right_count
        if total_valid > 10 and left_count > 0.15 * total_valid and right_count > 0.15 * total_valid:
            layout["columns"] = 2
        else:
            layout["columns"] = 1
    else:
        layout["columns"] = 1
        
    return layout

def calculate_fidelity_score(extracted_layout, active_layout):
    """
    Computes a layout match score comparing the original layout configuration
    against the generated template's active parameters.
    """
    scores = {
        "layout": 100.0,
        "font": 100.0,
        "spacing": 100.0,
        "color": 100.0
    }
    
    # 1. Layout Match (Columns / Alignments)
    ext_col = extracted_layout.get("columns", 1)
    act_col = active_layout.get("columns", 1)
    if ext_col != act_col:
        scores["layout"] -= 40.0
        
    ext_align = extracted_layout.get("header", {}).get("alignment", 0)
    act_align = active_layout.get("header", {}).get("alignment", 0)
    if ext_align != act_align:
        scores["layout"] -= 20.0
        
    scores["layout"] = max(0.0, scores["layout"])
    
    # 2. Font Size Match
    ext_name_sz = extracted_layout.get("header", {}).get("name_font_size", 18.0)
    act_name_sz = active_layout.get("header", {}).get("name_font_size", 18.0)
    name_diff = abs(ext_name_sz - act_name_sz) / ext_name_sz * 100.0 if ext_name_sz else 0.0
    
    ext_body_sz = extracted_layout.get("body", {}).get("font_size", 8.0)
    act_body_sz = active_layout.get("body", {}).get("font_size", 8.0)
    body_diff = abs(ext_body_sz - act_body_sz) / ext_body_sz * 100.0 if ext_body_sz else 0.0
    
    scores["font"] = max(0.0, 100.0 - (name_diff * 0.4 + body_diff * 0.6))
    
    # 3. Spacing & Margins Match
    ext_margin = extracted_layout.get("margins", {}).get("left", 36.0)
    act_margin = active_layout.get("margins", {}).get("left", 36.0)
    margin_diff = abs(ext_margin - act_margin) / ext_margin * 100.0 if ext_margin else 0.0
    scores["spacing"] = max(0.0, 100.0 - margin_diff)
    
    # 4. Color Match
    ext_color = str(extracted_layout.get("sections", {}).get("border_color", "#000000")).upper()
    act_color = str(active_layout.get("sections", {}).get("border_color", "#000000")).upper()
    
    # Extract hex colors cleanly for comparison
    def get_hex(c):
        m = re.search(r'(#[A-Fa-f0-9]{6}|#[A-Fa-f0-9]{3})', c)
        return m.group(1) if m else c
        
    if get_hex(ext_color) != get_hex(act_color):
        scores["color"] = 0.0
    else:
        scores["color"] = 100.0
        
    # Calculate weighted overall fidelity
    overall = (scores["layout"] * 0.35 + 
               scores["font"] * 0.25 + 
               scores["spacing"] * 0.20 + 
               scores["color"] * 0.20)
               
    return {
        "layout": int(scores["layout"]),
        "font": int(scores["font"]),
        "spacing": int(scores["spacing"]),
        "color": int(scores["color"]),
        "overall": int(overall)
    }
