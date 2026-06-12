import re
import json

_SAFE_TAGS = {"b", "i", "em", "strong", "u", "br", "font", "a", "sup", "sub"}

def sanitize_html(text: str) -> str:
    """Strip dangerous HTML tags, keeping only safe formatting tags for ReportLab."""
    if not text:
        return text
    # Remove script/style/img/iframe/object/embed tags entirely (with content for script/style)
    text = re.sub(r'<\s*(script|style)[^>]*>.*?</\s*\1\s*>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Remove dangerous self-closing or void tags
    text = re.sub(r'<\s*/?\s*(?:img|iframe|object|embed|link|meta|form|input|button|select|textarea)\b[^>]*/?>', '', text, flags=re.IGNORECASE)
    # Allow only safe tags; strip everything else
    def _tag_filter(m):
        tag_name = re.match(r'<\s*/?\s*(\w+)', m.group(0))
        if tag_name and tag_name.group(1).lower() in _SAFE_TAGS:
            return m.group(0)
        return ''
    text = re.sub(r'<[^>]+>', _tag_filter, text)
    return text

def resume_hash(d: dict, C: str, M: int, FS: float, tid: str, FT: str) -> str:
    raw = json.dumps(d, sort_keys=True) + f"|{C}|{M}|{FS}|{tid}|{FT}"
    return str(hash(raw))
