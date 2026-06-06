import os
import json
from resume_builder.templates import get_template_class

def build_pdf(data=None, template_id="sejal_original", pdf_filename=None, accent_color="#2563EB", font_scale=1.0, margin_size=20, auto_compress=True, allow_multi_page=False, aggressive_compact=False, layout_locked=False):
    """
    Compiles a PDF resume using a selected template style, with smart layout compression.
    
    Args:
        data (dict): The resume data config. If None, loaded from resume.json
        template_id (str): The ID of the template to use (default: sejal_original)
        pdf_filename (str): Name of output PDF. If None, derived dynamically.
        accent_color (str): Theme accent color in hex format.
        font_scale (float): Scale factor for layout fonts.
        margin_size (float): Page margin in points.
        auto_compress (bool): Automatically scale down font/margins/spacings to fit in 1 page.
        allow_multi_page (bool): Permit the resume to spill over to page 2+ in original scale.
        aggressive_compact (bool): If True, allows font sizes to shrink below 10pt (up to 0.75x).
        layout_locked (bool): If True, bypasses compression and locks margins/fonts to defaults.
        
    Returns:
        (bool, str): A tuple containing (success_status, warning_or_error_msg)
    """
    # 1. Load data from resume.json if not provided
    if data is None:
        try:
            with open("resume.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            msg = f"Failed to load resume.json: {e}"
            print(f"\n[ERROR] {msg}")
            print("Please make sure resume.json exists and is valid JSON.\n")
            return False, msg
            
    # 2. Dynamically determine pdf filename if not provided
    if pdf_filename is None:
        name = data.get("personal", {}).get("name", "Resume")
        sanitized_name = "".join([c if c.isalnum() else "_" for c in name]).strip("_")
        while "__" in sanitized_name:
            sanitized_name = sanitized_name.replace("__", "_")
        pdf_filename = f"{sanitized_name}_Resume.pdf" if sanitized_name else "Resume.pdf"
        
    # 3. Load the template class
    try:
        template_class = get_template_class(template_id)
        template_instance = template_class()
    except Exception as e:
        msg = f"Failed to load template '{template_id}': {e}"
        print(f"\n[ERROR] {msg}")
        return False, msg
        
    # 4. Smart Content Fitting Compression Configuration
    scale = font_scale
    margin = margin_size
    spacing = 1.0
    padding = 1.0
    
    # Define sequential layout optimization parameter steps
    if layout_locked:
        steps = [(1.0, 1.0, margin_size, 1.0)]
        auto_compress = False
    else:
        steps = [
            # (spacing_scale, padding_scale, margin_size, font_scale)
            (1.0, 1.0, margin_size, font_scale),       # Step 0: Original/default layout
            (0.85, 1.0, margin_size, font_scale),      # Step 1: Reduce spacing first
            (0.70, 1.0, margin_size, font_scale),      # Step 2: Reduce spacing further
            (0.60, 0.85, margin_size, font_scale),     # Step 3: Reduce spacing & begin padding reduction
            (0.50, 0.70, margin_size, font_scale),     # Step 4: Reduce spacing & padding further
            (0.50, 0.70, max(12, margin_size-4), font_scale),  # Step 5: Reduce margins slightly
            (0.50, 0.60, 12, font_scale),              # Step 6: Reduce padding & margins to limits
        ]
        
        # Readability Safeguard: If user allows aggressive compact mode, we add font scaling steps down to 0.75
        # Otherwise, we allow font scaling down to 0.80 (still readable at ~8pt) to fit all content sections
        min_allowable_font = 0.75 if aggressive_compact else 0.80
        
        if scale > min_allowable_font:
            curr_scale = scale
            while curr_scale > min_allowable_font:
                curr_scale = max(min_allowable_font, curr_scale - 0.05)
                # Add steps with reduced font size alongside optimized spacing/padding/margins
                steps.append((0.50, 0.60, 12, curr_scale))
            
    success = False
    msg = None
    num_pages = 1
    applied_step = 0
    
    # Compilation & Fitting loop
    for i, (s_scale, p_scale, m_size, f_scale) in enumerate(steps):
        applied_step = i
        scale = f_scale
        margin = m_size
        spacing = s_scale
        padding = p_scale
        
        success, msg = template_instance.generate(
            data=data,
            pdf_filename=pdf_filename,
            accent_color=accent_color,
            font_scale=scale,
            margin_size=margin,
            spacing_scale=spacing,
            padding_scale=padding,
            layout_locked=layout_locked
        )
        
        if not success:
            # Layout formatting or ReportLab compile error: stop immediately
            return False, msg
            
        # Verify page count
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_filename)
            num_pages = len(reader.pages)
        except Exception:
            num_pages = 1
            
        # Exit loop if:
        # - Content fits on exactly 1 page
        # - Auto-compression is disabled
        # - User explicitly allowed multi-page overflow
        if num_pages <= 1 or not auto_compress or allow_multi_page:
            break
            
    # Recompile with original styles if multi-page is explicitly allowed
    if num_pages > 1 and allow_multi_page:
        success, msg = template_instance.generate(
            data=data,
            pdf_filename=pdf_filename,
            accent_color=accent_color,
            font_scale=font_scale,
            margin_size=margin_size,
            spacing_scale=1.0,
            padding_scale=1.0,
            layout_locked=layout_locked
        )
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_filename)
            num_pages = len(reader.pages)
        except:
            pass
        msg = f"Multi-page spillover allowed. Resume spans {num_pages} pages."
    elif num_pages > 1:
        msg = "This resume contains significantly more content than recommended."
    elif applied_step > 0:
        msg = f"Auto-compressed layout: spacing={spacing:.2f}x, padding={padding:.2f}x, margin={margin}pt, font={scale:.2f}x."
        
    if success:
        try:
            import streamlit as st
            st.session_state.compiled_params = {
                "font_scale": scale,
                "margin_size": margin,
                "spacing_scale": spacing,
                "padding_scale": padding,
                "accent_color": accent_color,
                "layout_locked": layout_locked
            }
        except:
            pass
        print(f"Resume PDF compiled using template '{template_id}'. pages={num_pages}")
        if msg:
            print(f"[STATUS] {msg}")
    else:
        print(f"[ERROR] Failed to compile PDF: {msg}")
        
    return success, msg
