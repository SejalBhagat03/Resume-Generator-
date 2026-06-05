import sys
import os

# Append current directory to path to support running generate_resume.py directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from resume_builder.generators.pdf_generator import build_pdf

def generate_pdf(data=None, pdf_filename=None, accent_color="#2563EB", font_scale=1.0, margin_size=20):
    """
    Backwards-compatible wrapper around the new modular platform PDF layout engine.
    Uses 'sejal_original' template style to output identical PDF.
    """
    return build_pdf(
        data=data,
        template_id="sejal_original",
        pdf_filename=pdf_filename,
        accent_color=accent_color,
        font_scale=font_scale,
        margin_size=margin_size
    )

if __name__ == "__main__":
    generate_pdf()
