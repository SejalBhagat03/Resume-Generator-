import os
import sys
import glob
import json

# Setup paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from core.pdf_engine import build_pdf

def main():
    json_dir = os.path.join(PROJECT_ROOT, "exports", "json")
    pdf_dir = os.path.join(PROJECT_ROOT, "exports", "pdf")
    
    os.makedirs(pdf_dir, exist_ok=True)
    
    json_files = glob.glob(os.path.join(json_dir, "*.json"))
    
    if not json_files:
        print("No JSON files found to compile.")
        return

    for json_path in json_files:
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Read metadata
            meta = data.get("metadata", {})
            template = meta.get("template", "sejal_original")
            color = meta.get("color", "#2563EB")
            margins = meta.get("margins", 20)
            fscale = meta.get("fscale", 1.0)
            fitting = meta.get("fitting", "Auto Compress")
            
            auto_compress = fitting == "Auto Compress"
            allow_multi = fitting == "Multi-Page"
            
            base_name = os.path.basename(json_path)
            pdf_name = os.path.splitext(base_name)[0] + ".pdf"
            pdf_path = os.path.join(pdf_dir, pdf_name)
            
            success, msg = build_pdf(
                data=data,
                template_id=template,
                pdf_filename=pdf_path,
                accent_color=color,
                font_scale=fscale,
                margin_size=margins,
                auto_compress=auto_compress,
                allow_multi_page=allow_multi
            )
            
            if success:
                print(f"Successfully compiled: {pdf_name}")
            else:
                print(f"Failed to compile {pdf_name}: {msg}")
                sys.exit(1) # Fail the CI pipeline if a compilation fails
                
        except Exception as e:
            print(f"Error processing {os.path.basename(json_path)}: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
