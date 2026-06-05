import os
import json
import importlib

# Dictionary mapping template IDs to registration details
TEMPLATES = {}

def register_templates():
    templates_dir = os.path.dirname(__file__)
    for item in os.listdir(templates_dir):
        item_path = os.path.join(templates_dir, item)
        if os.path.isdir(item_path) and not item.startswith("__"):
            meta_path = os.path.join(item_path, "metadata.json")
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                    
                    TEMPLATES[item] = {
                        "id": item,
                        "name": metadata.get("name", item.replace("_", " ").title()),
                        "description": metadata.get("description", ""),
                        "ats_friendly": metadata.get("ats_friendly", False),
                        "module_path": f"resume_builder.templates.{item}.template",
                        "metadata": metadata
                    }
                except Exception as e:
                    # Log internally, fallback gracefully
                    pass

# Register all templates present in subfolders on import
register_templates()

def get_template_class(template_id):
    if template_id not in TEMPLATES:
        # Fall back to sejal_original if not found
        template_id = "sejal_original"
        if template_id not in TEMPLATES:
            raise ValueError(f"Default template 'sejal_original' is not registered.")
    
    info = TEMPLATES[template_id]
    module = importlib.import_module(info["module_path"])
    
    from resume_builder.templates.base import BaseTemplate
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, type) and issubclass(obj, BaseTemplate) and obj is not BaseTemplate:
            return obj
            
    raise AttributeError(f"No BaseTemplate subclass found in template module '{info['module_path']}'")
