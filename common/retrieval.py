import json
import math
import re
from collections import Counter
from functools import lru_cache

from common.llm import embed

CHUNKS_PATH = "data/chunks.jsonl"
VECTORS_PATH = "data/embeddings.jsonl"


def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


@lru_cache(maxsize=1)
def load_index():
    chunks = {}
    for line in open(CHUNKS_PATH):
        c = json.loads(line)
        chunks[c["chunk_id"]] = c

    vectors = {}
    for line in open(VECTORS_PATH):
        v = json.loads(line)
        vectors[v["chunk_id"]] = v["vector"]

    docs = {cid: tokenize(c["text"]) for cid, c in chunks.items()}

    df = Counter()
    for toks in docs.values():
        df.update(set(toks))

    n = len(docs)
    avgdl = sum(len(t) for t in docs.values()) / n
    idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    return chunks, vectors, docs, idf, avgdl


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb)


def bm25_score(query, toks, idf, avgdl, k1=1.5, b=0.75):
    tf = Counter(toks)
    dl = len(toks)
    score = 0.0
    for t in tokenize(query):
        if t not in tf:
            continue
        f = tf[t]
        score += idf.get(t, 0) * (f * (k1 + 1)) / (f + k1 * (1 - b + b * dl / avgdl))
    return score


def rrf(vec_scores, kw_scores, k=60):
    """Reciprocal Rank Fusion: combine rankings, ignore score magnitudes."""
    vec_rank = {
        cid: i
        for i, cid in enumerate(sorted(vec_scores, key=vec_scores.get, reverse=True))
    }
    kw_rank = {
        cid: i
        for i, cid in enumerate(sorted(kw_scores, key=kw_scores.get, reverse=True))
    }
    n = len(vec_scores)
    return {
        cid: 1 / (k + vec_rank.get(cid, n)) + 1 / (k + kw_rank.get(cid, n))
        for cid in vec_scores
    }


def retrieve(query, top_k=5, main_only=False, max_page=47):
    chunks, vectors, docs, idf, avgdl = load_index()
    qv = embed(query)

    vec_scores = {}
    kw_scores = {}

    for cid, c in chunks.items():
        if main_only and (c["is_appendix"] or c["start_page"] > max_page):
            continue
        vec_scores[cid] = cosine(qv, vectors[cid])
        kw_scores[cid] = bm25_score(query, docs[cid], idf, avgdl)

    fused = rrf(vec_scores, kw_scores)
    scored = sorted(((s, cid) for cid, s in fused.items()), reverse=True)

    results = []
    for score, cid in scored[:top_k]:
        c = dict(chunks[cid])
        c["score"] = round(score, 5)
        results.append(c)
    return results