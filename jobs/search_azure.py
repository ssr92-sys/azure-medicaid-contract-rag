import sys

from common.azsearch import retrieve

args = [a for a in sys.argv[1:] if not a.startswith("--")]
main_only = "--main-only" in sys.argv
query = args[0] if args else "when does this agreement terminate?"

print(f"query: {query}   (main_only={main_only})\n")

for r in retrieve(query, top_k=5, main_only=main_only):
    print(f"{r['score']:.5f}  {r['chunk_id']}  p{r['start_page']}  {r['section_path'][:60]}")
    print(f"        {r['text'][:150].strip()}...\n")