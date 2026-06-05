import re

def compile_custom_html(html_code, data):
    """
    Renders custom HTML templates by substituting bracket markers with JSON resume data.
    Supports list loops using {{#each <key>}} ... {{/each}} notation.
    """
    # 1. Compile the loops: {{#each experience}} ... {{/each}}
    loop_pattern = re.compile(r'\{\{\s*#each\s+([a-zA-Z0-9_]+)\s*\}\}(.*?)\{\{\s*/each\s*\}\}', re.DOTALL)
    
    def replace_loop(match):
        key = match.group(1)
        sub_template = match.group(2)
        items = data.get(key, [])
        if not isinstance(items, list):
            return ""
            
        rendered_items = []
        for item in items:
            rendered_item = sub_template
            if isinstance(item, dict):
                # Nested list rendering (e.g. bullets loop)
                bullet_loops = re.findall(r'\{\{\s*#each\s+bullets\s*\}\}(.*?)\{\{\s*/each\s*\}\}', rendered_item, re.DOTALL)
                for b_sub in bullet_loops:
                    bullets_rendered = "".join([b_sub.replace("{{this}}", str(b)) for b in item.get("bullets", [])])
                    rendered_item = re.sub(r'\{\{\s*#each\s+bullets\s*\}\}.*?\{\{\s*/each\s*\}\}', bullets_rendered, rendered_item, flags=re.DOTALL)
                
                # Replace properties
                for var_key, var_val in item.items():
                    if isinstance(var_val, str):
                        rendered_item = re.sub(r'\{\{\s*' + var_key + r'\s*\}\}', var_val, rendered_item)
            elif isinstance(item, str):
                rendered_item = rendered_item.replace("{{this}}", item)
            rendered_items.append(rendered_item)
        return "".join(rendered_items)
        
    html_rendered = loop_pattern.sub(replace_loop, html_code)
    
    # 2. Compile flat personal fields (e.g. {{personal.name}}, {{name}})
    personal = data.get("personal", {})
    for k, v in personal.items():
        if isinstance(v, str):
            html_rendered = re.sub(r'\{\{\s*personal\.' + k + r'\s*\}\}', v, html_rendered)
            html_rendered = re.sub(r'\{\{\s*' + k + r'\s*\}\}', v, html_rendered)
        elif isinstance(v, dict):
            for sk, sv in v.items():
                if isinstance(sv, str):
                    html_rendered = re.sub(r'\{\{\s*personal\.' + k + r'\.' + sk + r'\s*\}\}', sv, html_rendered)
                    html_rendered = re.sub(r'\{\{\s*' + k + r'\.' + sk + r'\s*\}\}', sv, html_rendered)
                
    # Replace other top-level fields
    for k, v in data.items():
        if isinstance(v, str):
            html_rendered = re.sub(r'\{\{\s*' + k + r'\s*\}\}', v, html_rendered)
            
    # Clean up uncompiled brackets
    html_rendered = re.sub(r'\{\{\s*.*?\s*\}\}', '', html_rendered)
    
    return html_rendered

def analyze_html_template_styles(html_code):
    """
    Analyzes an uploaded HTML template's layout to determine column structure, 
    font sizes, and estimate appropriate word count guidance metrics.
    """
    analysis = {
        "columns": 1,
        "average_font_size": 11.0,
        "text_regions": [],
        "recommendations": {
            "summary": "40-80 words",
            "experience": "15-30 words per bullet",
            "projects": "20-60 words per bullet",
            "skills": "5-15 skills total"
        }
    }
    
    # 1. Identify text regions / placeholder keys
    placeholders = re.findall(r'\{\{\s*([a-zA-Z0-9_\.]+)\s*\}\}', html_code)
    analysis["text_regions"] = list(set([p for p in placeholders if not p.startswith(("#", "/"))]))
    
    # 2. Heuristically detect column grids
    grid_indicators = ["display: grid", "grid-template-columns", "float: left", "width: 50%", "width: 30%", "width: 40%", "flex: 1", "flex-grow", "column-count", "col-md", "col-lg", "col-sm", "<td>"]
    indicate_count = sum(1 for indicator in grid_indicators if indicator in html_code.lower())
    if indicate_count >= 2:
        analysis["columns"] = 2
        
    # 3. Detect font-size declarations
    sizes = []
    font_size_matches = re.findall(r'font-size\s*:\s*(\d+)(px|pt|rem|em)', html_code.lower())
    for val, unit in font_size_matches:
        try:
            fval = float(val)
            if unit in ["rem", "em"]:
                fval = fval * 16.0 # standard browser baseline
            sizes.append(fval)
        except ValueError:
            pass
            
    if sizes:
        analysis["average_font_size"] = sum(sizes) / len(sizes)
        
    # 4. Generate recommendations based on structural properties
    if analysis["columns"] == 2:
        analysis["recommendations"] = {
            "summary": "30-60 words",
            "experience": "10-25 words per bullet",
            "projects": "15-40 words per bullet",
            "skills": "4-10 skills total"
        }
    elif analysis["average_font_size"] >= 13.0:
        analysis["recommendations"] = {
            "summary": "30-50 words",
            "experience": "10-20 words per bullet",
            "projects": "15-30 words per bullet",
            "skills": "5-10 skills total"
        }
        
    return analysis
