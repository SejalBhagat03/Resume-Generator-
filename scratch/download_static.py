import os
import urllib.request

static_dir = r"c:\Users\HP\Documents\resume-generator\resume_builder\data\static"
os.makedirs(static_dir, exist_ok=True)

urls = {
    "pdf.min.js": "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.min.js",
    "pdf.worker.min.js": "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js"
}

for name, url in urls.items():
    path = os.path.join(static_dir, name)
    print(f"Downloading {url} to {path}...")
    urllib.request.urlretrieve(url, path)
print("Done!")
