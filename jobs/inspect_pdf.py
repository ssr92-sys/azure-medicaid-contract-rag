from pypdf import PdfReader

reader = PdfReader("data/raw/md_healthchoice_2026.pdf")

pages = []
for i, page in enumerate(reader.pages):
    text = page.extract_text() or ""
    pages.append({"page": i + 1, "text": text})

total_chars = sum(len(p["text"]) for p in pages)
empty = sum(1 for p in pages if len(p["text"].strip()) < 50)

print(f"pages: {len(pages)}")
print(f"total characters: {total_chars:,}")
print(f"roughly {total_chars // 4:,} tokens")
print(f"near-empty pages: {empty}")