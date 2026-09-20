import re
from difflib import SequenceMatcher

CITE = re.compile(r"\[(md2026-\d{4})\]")
QUOTE = re.compile(r'"([^"]{20,})"')


def normalize(text):
    return re.sub(r"\s+", " ", text.lower()).strip()


def best_match(quote, source):
    """Highest similarity of quote against any same-length window of source."""
    q, s = normalize(quote), normalize(source)
    if q in s:
        return 1.0
    n = len(q)
    if n > len(s):
        return SequenceMatcher(None, q, s).ratio()
    best = 0.0
    for i in range(0, len(s) - n + 1, max(1, n // 4)):
        r = SequenceMatcher(None, q, s[i:i + n]).ratio()
        if r > best:
            best = r
    return best


def verify(answer, chunks, threshold=0.85):
    by_id = {c["chunk_id"]: c for c in chunks}
    cited = CITE.findall(answer)

    results = []
    for quote in QUOTE.findall(answer):
        fragments = [f.strip() for f in re.split(r"\s*\.\.\.\s*", quote)
                     if len(f.strip()) >= 20]
        if not fragments:
            fragments = [quote]

        scores = []
        for cid in cited:
            if cid not in by_id:
                continue
            frag_scores = [best_match(f, by_id[cid]["text"]) for f in fragments]
            scores.append((min(frag_scores), cid))

        if not scores:
            results.append({"quote": quote, "score": 0.0,
                            "chunk_id": None, "verified": False})
            continue

        score, cid = max(scores)
        results.append({"quote": quote, "score": round(score, 3),
                        "chunk_id": cid, "verified": score >= threshold})
    return results