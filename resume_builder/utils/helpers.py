import time

def margin_label(m: int) -> tuple:
    if m <= 12:   return ("Tight layout",   "eff-tight")
    if m <= 18:   return ("Compact layout", "eff-compact")
    if m <= 24:   return ("Balanced",       "eff-balanced")
    return             ("Spacious layout", "eff-spacious")

def fscale_label(fs: float) -> tuple:
    if fs <= 0.80: return ("More content per page", "eff-compact")
    if fs <= 0.95: return ("Slightly compact",       "eff-compact")
    if fs <= 1.05: return ("Standard readability",   "eff-standard")
    if fs <= 1.15: return ("Larger text",            "eff-balanced")
    return              ("Large text / fewer items", "eff-spacious")

def format_relative_time(timestamp: float) -> str:
    diff = time.time() - timestamp
    if diff < 60:
        return "Just now"
    elif diff < 3600:
        mins = int(diff / 60)
        return f"{mins} minute{'s' if mins > 1 else ''} ago"
    elif diff < 86400:
        hours = int(diff / 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff < 172800:
        return "Yesterday"
    else:
        days = int(diff / 86400)
        if days < 7:
            return f"{days} day{'s' if days > 1 else ''} ago"
        else:
            struct = time.localtime(timestamp)
            return time.strftime("%d %b %Y", struct)
