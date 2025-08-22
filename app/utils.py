import re

def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s or 'cafe'
