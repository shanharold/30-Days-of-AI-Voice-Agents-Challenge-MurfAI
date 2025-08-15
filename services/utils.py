def sanitize_text(s: str) -> str:
    if not isinstance(s, str):
        s = str(s)
    s = s.replace("\r", " ").replace("\n", " ")
    s = " ".join(s.split())
    return s.strip()

def clamp_text(s: str, max_len: int) -> str:
    return s if len(s) <= max_len else s[:max_len]

def split_into_chunks(text: str, max_len: int):
    text = text.strip()
    if len(text) <= max_len:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_len, len(text))
        if end < len(text):
            space = text.rfind(" ", start, end)
            if space != -1 and space > start:
                end = space
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end
    return chunks if chunks else [""]