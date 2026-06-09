import os
from pypdf import PdfReader

pdf_path = 'Sejal_Bhagat_Resume.pdf'
reader = PdfReader(pdf_path)
page = reader.pages[0]

elements = []
def visitor(text, cm, tm, font_dict, font_size):
    stripped = text.strip()
    if stripped:
        elements.append({
            'text': stripped,
            'cm': cm,
            'tm': tm,
            'size': font_size
        })

page.extract_text(visitor_text=visitor)

targets = ["B.Tech", "12th", "10th", "2022", "2020", "90%", "87%"]
for el in elements:
    if any(t in el['text'] for t in targets):
        print(f"text: {el['text']}")
        print(f"  cm: {el['cm']}")
        print(f"  tm: {el['tm']}")
