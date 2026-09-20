import json
import os

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient

load_dotenv()

client = SearchClient(
    endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
    index_name=os.environ["AZURE_SEARCH_INDEX"],
    credential=DefaultAzureCredential(),
)

chunks = {}
for line in open("data/chunks.jsonl"):
    c = json.loads(line)
    chunks[c["chunk_id"]] = c

vectors = {}
for line in open("data/embeddings.jsonl"):
    v = json.loads(line)
    vectors[v["chunk_id"]] = v["vector"]

docs = []
for cid, c in chunks.items():
    if cid not in vectors:
        print(f"skipping {cid} — no vector")
        continue
    docs.append({
        "chunk_id": cid,
        "text": c["text"],
        "section_path": c["section_path"],
        "heading": c["heading"],
        "start_page": c["start_page"],
        "end_page": c["end_page"],
        "is_appendix": c["is_appendix"],
        "source_file": c["source_file"],
        "vector": vectors[cid],
    })

print(f"uploading {len(docs)} documents")

BATCH = 100
uploaded = 0
for i in range(0, len(docs), BATCH):
    batch = docs[i:i + BATCH]
    result = client.upload_documents(documents=batch)
    ok = sum(1 for r in result if r.succeeded)
    uploaded += ok
    print(f"  {i + len(batch)}/{len(docs)}  ({ok} succeeded)")

print(f"uploaded {uploaded}/{len(docs)}")