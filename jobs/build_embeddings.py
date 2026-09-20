import json
import os
import time

from common.llm import embed

IN = "data/chunks.jsonl"
OUT = "data/embeddings.jsonl"

if os.path.exists(OUT):
    print(f"{OUT} exists — delete it to re-embed")
    raise SystemExit

chunks = [json.loads(l) for l in open(IN)]
print(f"embedding {len(chunks)} chunks")

t0 = time.time()
ok = 0

with open(OUT, "w") as out:
    for i, c in enumerate(chunks, 1):
        try:
            vec = embed(c["text"])
            out.write(json.dumps({"chunk_id": c["chunk_id"], "vector": vec}) + "\n")
            out.flush()
            ok += 1
        except Exception as e:
            print(f"[{i}] FAILED {c['chunk_id']}: {type(e).__name__}: {e}")

        if i % 50 == 0:
            print(f"  {i}/{len(chunks)}  {time.time()-t0:.0f}s")

print(f"embedded {ok}/{len(chunks)} in {time.time()-t0:.0f}s")