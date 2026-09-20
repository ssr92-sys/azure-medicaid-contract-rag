import re

HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
PAGENUM = re.compile(r'<!--\s*PageNumber="Page (\d+) of \d+"\s*-->')
COMMENT = re.compile(r"<!--.*?-->", re.S)
NOISE = re.compile(r"^(2026 Maryland HealthChoice|Calendar Year \d{4})", re.I)


def split_sections(md):
    sections = []
    trail = {}
    buf = []
    current = "(preamble)"
    page = 1
    start_page = 1

    def flush():
        text = "\n".join(buf).strip()
        if text:
            sections.append({
                "heading": current,
                "trail": dict(trail),
                "text": text,
                "start_page": start_page,
                "end_page": page,
            })

    for line in md.split("\n"):
        pm = PAGENUM.search(line)
        if pm:
            page = int(pm.group(1))

        m = HEADING.match(line)
        if m:
            level, title = len(m.group(1)), m.group(2).strip()
            if NOISE.match(title):
                continue
            flush()
            buf = []
            start_page = page
            trail[level] = title
            for lvl in list(trail):
                if lvl > level:
                    del trail[lvl]
            current = title
        else:
            buf.append(line)

    flush()
    return sections


def split_by_size(text, target=3000, overlap=400):
    if len(text) <= target:
        return [text]
    out, i = [], 0
    while i < len(text):
        end = i + target
        if end < len(text):
            space = text.rfind(" ", i + target - 200, end)
            if space > i:
                end = space
        out.append(text[i:end])
        i = end - overlap
    return out


def build_chunks(md, source_file, target=3000, overlap=400):
    chunks = []
    for s in split_sections(md):
        clean = COMMENT.sub(" ", s["text"])
        clean = re.sub(r"[ \t]+", " ", clean)

        path = " > ".join(s["trail"][k] for k in sorted(s["trail"]))
        is_appendix = s["start_page"] > 47

        for j, piece in enumerate(split_by_size(clean, target, overlap)):
            piece = piece.strip()
            if len(piece) < 150:
                continue
            chunks.append({
                "text": piece,
                "heading": s["heading"],
                "section_path": path,
                "part": j,
                "start_page": s["start_page"],
                "end_page": s["end_page"],
                "is_appendix": is_appendix,
                "source_file": source_file,
            })
    return chunks