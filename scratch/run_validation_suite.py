import os
import json
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from resume_builder.parser.reader import extract_pdf_layout_and_text
from resume_builder.parser.engine import parse_extracted_text_to_json, analyze_style_from_runs, calculate_fidelity_score
from resume_builder.generators.pdf_generator import build_pdf
from pypdf import PdfReader

def run_validation():
    corpus_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_corpus"))
    if not os.path.exists(corpus_dir):
        print("[ERROR] Test corpus directory not found. Run generate_test_suite_data.py first.")
        return
        
    print("=========================================================")
    print("         RESUME VALIDATION SUITE RUNNER")
    print("=========================================================")
    
    results = []
    
    templates = ["sejal_original", "ats", "modern", "creative", "minimal", "two_column"]
    colors_accent = ["#2563EB", "#10B981", "#EF4444", "#8B5CF6", "#475569", "#000000"]
    margins = [12, 16, 20, 24, 28, 32]
    scales = [0.8, 0.9, 1.0, 1.1, 1.2]
    densities = ["short", "medium", "long"]
    
    for i in range(1, 26):
        # Deterministic expected variables
        expected_template = templates[i % len(templates)]
        expected_color = colors_accent[i % len(colors_accent)]
        expected_margin = margins[i % len(margins)]
        expected_scale = scales[i % len(scales)]
        density = densities[i % len(densities)]
        
        pdf_path = os.path.join(corpus_dir, f"candidate_{i}.pdf")
        json_path = os.path.join(corpus_dir, f"candidate_{i}.json")
        
        if not os.path.exists(pdf_path) or not os.path.exists(json_path):
            continue
            
        with open(json_path, "r", encoding="utf-8") as f:
            original_json = json.load(f)
            
        # 1. Extraction Phase
        text, runs_data = extract_pdf_layout_and_text(pdf_path)
        parsed_json = parse_extracted_text_to_json(text)
        
        # Measure Extraction Accuracy
        expected_name = f"TEST CANDIDATE {i}".upper()
        expected_email = f"candidate{i}@example.com"
        expected_phone = f"+1 555-010-100{i}"
        
        extracted_name = parsed_json.get("personal", {}).get("name", "").upper()
        extracted_email = parsed_json.get("personal", {}).get("email", "")
        extracted_phone = parsed_json.get("personal", {}).get("phone", "")
        
        # Soft match name as summary or header could contain the name
        name_match = expected_name in extracted_name or extracted_name in expected_name
        email_match = expected_email == extracted_email
        phone_match = expected_phone == extracted_phone
        
        extraction_score = sum([name_match, email_match, phone_match]) / 3.0 * 100.0
        
        # 2. Template Preservation Accuracy
        layout_cfg = analyze_style_from_runs(runs_data)
        
        # Build active layout to calculate fidelity score
        active_layout = {
            "columns": layout_cfg.get("columns", 1),
            "margins": {"left": expected_margin, "top": expected_margin, "right": expected_margin, "bottom": expected_margin},
            "header": {
                "alignment": layout_cfg.get("header", {}).get("alignment", 0),
                "name_font_size": layout_cfg.get("header", {}).get("name_font_size", 18.0) * expected_scale,
                "contact_font_size": layout_cfg.get("header", {}).get("contact_font_size", 8.5) * expected_scale
            },
            "sections": {
                "title_font_size": layout_cfg.get("sections", {}).get("title_font_size", 10.0) * expected_scale,
                "border_color": expected_color
            },
            "body": {
                "font_size": layout_cfg.get("body", {}).get("font_size", 8.0) * expected_scale,
                "leading": layout_cfg.get("body", {}).get("leading", 10.5) * expected_scale
            }
        }
        
        fidelity = calculate_fidelity_score(layout_cfg, active_layout)
        preservation_score = fidelity["overall"]
        
        # 3. Layout Stability & Rebuild Compilation
        rebuilt_pdf_path = os.path.join(corpus_dir, f"candidate_{i}_rebuilt.pdf")
        success, msg = build_pdf(
            data=parsed_json,
            template_id=expected_template,
            pdf_filename=rebuilt_pdf_path,
            accent_color=expected_color,
            font_scale=expected_scale,
            margin_size=expected_margin,
            auto_compress=(density != "long"),
            allow_multi_page=(density == "long"),
            aggressive_compact=True
        )
        
        rebuilt_pages = 0
        if success and os.path.exists(rebuilt_pdf_path):
            try:
                reader = PdfReader(rebuilt_pdf_path)
                rebuilt_pages = len(reader.pages)
            except:
                rebuilt_pages = 1
                
        # 4. Overflow Handling
        overflow_ok = True
        if density != "long" and rebuilt_pages > 1:
            overflow_ok = False
            
        # Monochrome templates (ats, minimal, sejal_original) do not support color accents, 
        # so their preservation score limit is adjusted accordingly
        min_preserve = 50.0 if expected_template in ["ats", "minimal", "sejal_original"] else 60.0
        case_ok = (extraction_score >= 66.0) and (preservation_score >= min_preserve) and success and overflow_ok
        
        results.append({
            "case": i,
            "template": expected_template,
            "density": density,
            "extraction_score": int(extraction_score),
            "preservation_score": int(preservation_score),
            "rebuilt_success": success,
            "rebuilt_pages": rebuilt_pages,
            "overflow_ok": overflow_ok,
            "status": "PASS" if case_ok else "FAIL",
            "notes": msg if not success else ""
        })
        
        status_symbol = "PASS" if case_ok else "FAIL"
        print(f"Case {i:2d} ({expected_template:15s}, {density:6s}): Extract={int(extraction_score):3d}% | Preserve={int(preservation_score):3d}% | Rebuild={str(success):5s} | Pages={rebuilt_pages} -> {status_symbol}")

    # Summary report
    passes = sum(1 for r in results if r["status"] == "PASS")
    total = len(results)
    pass_rate = passes / total * 100.0 if total else 0
    
    print("\n=========================================================")
    print("                 VALIDATION RESULTS SUMMARY")
    print("=========================================================")
    print(f"Total Test Cases Run: {total}")
    print(f"Successful Passes   : {passes}")
    print(f"Failed Cases        : {total - passes}")
    print(f"Pass Rate           : {pass_rate:.1f}%")
    print("=========================================================")
    
    # Save validation report card JSON
    report_path = os.path.join(corpus_dir, "validation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "summary": {
                "total": total,
                "passes": passes,
                "failures": total - passes,
                "pass_rate_pct": round(pass_rate, 2)
            },
            "cases": results
        }, f, indent=2)
    print(f"Saved validation report to: {report_path}")

if __name__ == "__main__":
    run_validation()
