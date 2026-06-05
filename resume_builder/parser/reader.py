import zipfile
import xml.etree.ElementTree as ET
from pypdf import PdfReader

def extract_pdf_layout_and_text(pdf_file_or_path):
    """
    Extracts raw text and detailed layout text-runs (coordinates, font sizes) from a PDF,
    reconstructing reading flow by sorting and clustering columns when necessary.
    """
    try:
        reader = PdfReader(pdf_file_or_path)
        full_text = ""
        all_runs = []
        
        for page_idx, page in enumerate(reader.pages):
            page_runs = []
            
            def visitor_text(text, cm, tm, font_dict, font_size):
                t = text.strip()
                if t:
                    # Calculate absolute coordinates by transforming TM with CM
                    abs_x = tm[4] * cm[0] + tm[5] * cm[2] + cm[4]
                    abs_y = tm[4] * cm[1] + tm[5] * cm[3] + cm[5]
                    page_runs.append({
                        "text": text,
                        "x": abs_x,
                        "y": abs_y,
                        "font_size": font_size,
                        "font_name": font_dict.get("/BaseFont", "") if font_dict else ""
                    })
            
            page.extract_text(visitor_text=visitor_text)
            
            if page_runs:
                # Reconstruct this page's text order
                # Check for two columns by analyzing X coordinate spread
                x_coords = [r["x"] for r in page_runs]
                is_two_col = False
                if len(x_coords) > 10:
                    left_c = sum(1 for x in x_coords if x < 230)
                    right_c = sum(1 for x in x_coords if x >= 230)
                    if left_c > 0.15 * len(x_coords) and right_c > 0.15 * len(x_coords):
                        is_two_col = True
                
                def sort_and_join_runs(runs):
                    sorted_runs = sorted(runs, key=lambda r: r["y"], reverse=True)
                    lines = []
                    current_line = []
                    last_y = None
                    
                    for r in sorted_runs:
                        y = r["y"]
                        if last_y is None or abs(last_y - y) < 4:
                            current_line.append(r)
                        else:
                            current_line = sorted(current_line, key=lambda r: r["x"])
                            lines.append(current_line)
                            current_line = [r]
                        last_y = y
                    if current_line:
                        current_line = sorted(current_line, key=lambda r: r["x"])
                        lines.append(current_line)
                        
                    line_texts = []
                    for line in lines:
                        parts = []
                        for idx, r in enumerate(line):
                            txt = r["text"]
                            if idx > 0:
                                prev_txt = line[idx-1]["text"]
                                if not prev_txt.endswith(" ") and not txt.startswith(" "):
                                    parts.append(" ")
                            parts.append(txt)
                        line_texts.append("".join(parts))
                    return "\n".join(line_texts)
                
                if is_two_col:
                    left_runs = [r for r in page_runs if r["x"] < 230]
                    right_runs = [r for r in page_runs if r["x"] >= 230]
                    page_text = sort_and_join_runs(left_runs) + "\n" + sort_and_join_runs(right_runs)
                else:
                    page_text = sort_and_join_runs(page_runs)
                    
                full_text += page_text + "\n"
                all_runs.extend(page_runs)
            else:
                # Fallback to standard extraction if no runs found
                full_text += page.extract_text() + "\n"
                
        return full_text, all_runs
    except Exception as e:
        return f"Error parsing PDF: {e}", []

def extract_docx_layout_and_text(docx_file_or_path):
    """
    Extracts text and style details from a DOCX file using built-in XML parsing.
    """
    try:
        # DOCX is a ZIP container. We extract word/document.xml and word/styles.xml if available.
        with zipfile.ZipFile(docx_file_or_path) as docx:
            xml_content = docx.read('word/document.xml')
            root = ET.fromstring(xml_content)
            
            # XML Namespaces
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            
            paragraphs = []
            text_runs = []
            
            # Find margins from the section properties at the end of body
            margins = {"top": 72, "bottom": 72, "left": 72, "right": 72} # defaults in pt
            sectPr = root.find('.//w:sectPr', ns)
            if sectPr is not None:
                pgMar = sectPr.find('w:pgMar', ns)
                if pgMar is not None:
                    # DOCX measures margins in twentieths of a point (dxa)
                    # 1 pt = 20 dxa
                    def to_pt(dxa_val):
                        return float(dxa_val) / 20.0 if dxa_val else 72.0
                    margins["top"] = to_pt(pgMar.attrib.get(f'{{{ns["w"]}}}top'))
                    margins["bottom"] = to_pt(pgMar.attrib.get(f'{{{ns["w"]}}}bottom'))
                    margins["left"] = to_pt(pgMar.attrib.get(f'{{{ns["w"]}}}left'))
                    margins["right"] = to_pt(pgMar.attrib.get(f'{{{ns["w"]}}}right'))
            
                # Process all paragraphs
            for para in root.findall('.//w:p', ns):
                p_text = ""
                # Get paragraph alignment
                align = 0 # default left
                jc = para.find('.//w:jc', ns)
                if jc is not None:
                    val = jc.attrib.get(f'{{{ns["w"]}}}val', 'left')
                    if val == 'center':
                        align = 1
                    elif val in ['right', 'end']:
                        align = 2
                        
                # Extract text runs from paragraph
                p_font_size = 10.0 # default
                p_color = "#000000"
                p_bold = False
                
                # Paragraph shading
                pPr = para.find('.//w:pPr', ns)
                if pPr is not None:
                    shd = pPr.find('.//w:shd', ns)
                    if shd is not None:
                        val = shd.attrib.get(f'{{{ns["w"]}}}fill')
                        if val and val != "auto" and val != "clear":
                            p_color = f"#{val}"
                
                runs = para.findall('.//w:r', ns)
                for run in runs:
                    t_el = run.find('w:t', ns)
                    if t_el is not None and t_el.text:
                        r_text = t_el.text
                        p_text += r_text
                        
                        # Size in half points (sz)
                        sz = run.find('.//w:sz', ns)
                        if sz is not None:
                            val = sz.attrib.get(f'{{{ns["w"]}}}val')
                            if val:
                                p_font_size = float(val) / 2.0
                                
                        # Color
                        color = run.find('.//w:color', ns)
                        if color is not None:
                            val = color.attrib.get(f'{{{ns["w"]}}}val')
                            if val and val != "auto":
                                p_color = f"#{val}"
                                
                        # Shading (run-level background)
                        shd = run.find('.//w:shd', ns)
                        if shd is not None:
                            val = shd.attrib.get(f'{{{ns["w"]}}}fill')
                            if val and val != "auto" and val != "clear":
                                p_color = f"#{val}"
                                
                        # Bold
                        if run.find('.//w:b', ns) is not None:
                            p_bold = True
                            
                p_text_clean = p_text.strip()
                if p_text_clean:
                    paragraphs.append(p_text_clean)
                    text_runs.append({
                        "text": p_text_clean,
                        "font_size": p_font_size,
                        "color": p_color,
                        "bold": p_bold,
                        "alignment": align
                    })
                    
            full_text = "\n".join(paragraphs)
            return full_text, {"runs": text_runs, "margins": margins}
            
    except Exception as e:
        return f"Error parsing DOCX: {e}", {"runs": [], "margins": {}}

def extract_txt_text(txt_file_or_path):
    """
    Extracts text from a plain text file.
    """
    try:
        if isinstance(txt_file_or_path, str):
            with open(txt_file_or_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            return txt_file_or_path.read().decode("utf-8")
    except Exception as e:
        return f"Error reading text: {e}"
