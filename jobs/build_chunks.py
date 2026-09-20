import json
from common.chunking import build_chunks

SRC = "data/md_healthchoice_2026.md"

with open(SRC) as f:
    md = f.read()

chunks = build_chunks(md, source_file=SRC)

with open("data/chunks.jsonl", "w") as f:
    for i, c in enumerate(chunks):
        c["chunk_id"] = f"md2026-{i:04d}"
        f.write(json.dumps(c) + "\n")

sizes = [len(c["text"]) for c in chunks]
print(f"{len(chunks)} chunks")
print(f"min {min(sizes)}  avg {sum(sizes)//len(sizes)}  max {max(sizes)}")
print(f"appendix chunks: {sum(1 for c in chunks if c['is_appendix'])}")