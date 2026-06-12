import streamlit as st
import os
import re
import json

from resume_builder.parser.reader import (
    extract_txt_text,
    extract_pdf_layout_and_text,
    extract_docx_layout_and_text,
)
from resume_builder.parser.engine import (
    analyze_style_from_runs,
    segment_into_blocks,
    parse_mapped_blocks_to_json,
)

def render_pdf_thumbnail(pdf_b64: str, key: str):
    if not pdf_b64:
        st.markdown(
            '<div style="background: #FAFBFF; border-bottom: 1px solid #F1F5F9; height: 110px; display: flex; align-items: center; justify-content: center;">'
            '<span style="font-size: 2rem; color: #CBD5E1;">📄</span>'
            '</div>',
            unsafe_allow_html=True
        )
        return
        
    pdf_js_b64, pdf_worker_b64 = st.session_state.load_local_pdfjs_assets_fn()
    html_content = f"""<!DOCTYPE html>
    <html>
    <head>
    <script>
      const pdfJsContent = atob("{pdf_js_b64}");
      const scriptEl = document.createElement('script');
      scriptEl.textContent = pdfJsContent;
      document.head.appendChild(scriptEl);
    </script>
    <style>
      * {{ box-sizing: border-box; margin: 0; padding: 0; }}
      body, html {{
        background: #F8FAFC;
        overflow: hidden;
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
      }}
      #canvas-container {{
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #F8FAFC;
        padding: 5px;
      }}
      canvas {{
        max-width: 100%;
        max-height: 100%;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border: 1px solid #E2E8F0;
        border-radius: 4px;
        background: #fff;
      }}
    </style>
    </head>
    <body>
    <div id="canvas-container">
      <canvas id="thumbnail-canvas"></canvas>
    </div>
    <script>
      const pdfjsLib = window['pdfjs-dist/build/pdf'];
      
      const pdfWorkerContent = atob("{pdf_worker_b64}");
      const blob = new Blob([pdfWorkerContent], {{type: 'application/javascript'}});
      const workerURL = URL.createObjectURL(blob);
      pdfjsLib.GlobalWorkerOptions.workerSrc = workerURL;
    
      const base64PDF = "{pdf_b64}";
    
      function b64ToArr(b64) {{
        const raw = atob(b64);
        const arr = new Uint8Array(raw.length);
        for (let i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
        return arr;
      }}
    
      pdfjsLib.getDocument({{
        data: b64ToArr(base64PDF),
        standardFontDataUrl: 'https://cdn.jsdelivr.net/npm/pdfjs-dist@3.4.120/standard_fonts/'
      }}).promise.then(async (pdf) => {{
        const page = await pdf.getPage(1);
        const canvas = document.getElementById('thumbnail-canvas');
        const ctx = canvas.getContext('2d');
        
        const viewport = page.getViewport({{ scale: 1.0 }});
        const scale = Math.min(100 / viewport.height, 75 / viewport.width);
        const scaledViewport = page.getViewport({{ scale: scale * 2 }}); 
        
        canvas.height = scaledViewport.height;
        canvas.width = scaledViewport.width;
        canvas.style.height = (scaledViewport.height / 2) + 'px';
        canvas.style.width = (scaledViewport.width / 2) + 'px';
        
        await page.render({{ canvasContext: ctx, viewport: scaledViewport }}).promise;
      }}).catch(err => {{
        console.error('Thumbnail render error:', err);
      }});
    </script>
    </body>
    </html>"""
    
    import streamlit.components.v1 as components
    components.html(html_content, height=110, scrolling=False)

@st.dialog("Import Resume")
def show_import_dialog():
    
    st.markdown("Upload your existing resume (PDF, DOCX, or TXT) to extract its structure and text details.")
    
    if "wiz_step" not in st.session_state:
        st.session_state.wiz_step = "upload"
        
    if st.session_state.wiz_step == "upload":
        uf = st.file_uploader("Drop your resume file here", type=["pdf","docx","txt"], key="imp_file")
        do_ext = st.checkbox("Save as reusable template", value=True, key="imp_do_ext")
        tname  = st.text_input("Template name", "my_style", key="imp_tname")

        if uf and st.button("🚀 Extract & Import", type="primary", key="imp_go", use_container_width=True):
            with st.spinner("Analysing…"):
                tdir = os.path.join("resume_builder","data","temp")
                os.makedirs(tdir, exist_ok=True)
                tp = os.path.join(tdir, uf.name)
                with open(tp,"wb") as tf: tf.write(uf.getbuffer())
                ext = uf.name.rsplit(".",1)[-1].lower()
                txt, lcfg = "", None
                try:
                    if ext == "txt":
                        txt  = extract_txt_text(tp)
                        lcfg = {"margins":{"top":20,"bottom":20,"left":36,"right":36},
                                "header":{"alignment":0,"name_font_size":18.,"contact_font_size":8.5},
                                "sections":{"title_font_size":10.,"border_below":True,
                                            "border_above":False,"border_color":"#000000"},
                                "body":{"font_size":8.,"leading":10.5,"bullet_indent":15}}
                    elif ext == "pdf":
                        txt, runs = extract_pdf_layout_and_text(tp)
                        lcfg = analyze_style_from_runs(runs)
                    elif ext == "docx":
                        txt, dd = extract_docx_layout_and_text(tp)
                        lcfg = analyze_style_from_runs(dd.get("runs",[]),dd.get("margins"))
                except Exception as ex:
                    st.error(f"Extraction error: {ex}")
                finally:
                    try: os.remove(tp)
                    except: pass
                if txt:
                    st.session_state.wiz_blk  = segment_into_blocks(txt)
                    st.session_state.wiz_lay  = lcfg
                    st.session_state.wiz_step = "wizard"
                    st.session_state["_do_ext"] = do_ext
                    st.session_state["_tname"]  = tname
                    st.rerun()
                else:
                    st.error("No text found — try another format.")

    elif st.session_state.wiz_step == "wizard":
        st.markdown("**Review extracted sections — adjust categories if needed:**")
        CATS = {"personal":"👤 Personal","summary":"📝 Summary",
                "experience":"💼 Experience","projects":"🚀 Projects",
                "skills":"🛠️ Skills","education":"🎓 Education",
                "achievements":"🏆 Achievements",
                "position_of_responsibility":"🤝 Positions","ignore":"❌ Ignore"}
        mapped = []
        for i, b in enumerate(st.session_state.wiz_blk):
            ic = b.get("inferred_category","ignore")
            di = list(CATS).index(ic) if ic in CATS else len(CATS)-1
            st.markdown(f"**`{b['header']}`**")
            sc = st.selectbox("Category",list(CATS),format_func=lambda x:CATS[x],
                              index=di,key=f"wz_{i}")
            st.text_area("Preview","\n".join(b["lines"][:3]),
                         height=60,disabled=True,key=f"wz_pv{i}")
            mapped.append({"header":b["header"],"category":sc,"lines":b["lines"]})

        wz1, wz2 = st.columns(2)
        with wz1:
            if st.button("❌ Cancel", key="wz_cancel", use_container_width=True):
                st.session_state.wiz_step = "upload"
                st.session_state.wiz_blk  = []
                st.session_state.wiz_lay  = None
                st.rerun()
        with wz2:
            if st.button("✅ Confirm & Import", type="primary", key="wz_ok", use_container_width=True):
                parsed = parse_mapped_blocks_to_json(mapped)
                st.session_state.push_undo_fn(st.session_state.resume)
                st.session_state.resume = parsed
                if st.session_state.get("_do_ext") and st.session_state.wiz_lay:
                    tn = st.session_state.get("_tname","my_style")
                    rn = st.session_state.save_extracted_template_fn(st.session_state.wiz_lay, tn)
                    st.session_state.template = rn
                st.session_state.save_to_disk_fn(parsed)
                st.session_state.last_hash = ""
                st.session_state.wiz_step = "upload"
                st.session_state.wiz_blk  = []
                st.session_state.wiz_lay  = None
                st.session_state.show_import = False
                st.rerun()
