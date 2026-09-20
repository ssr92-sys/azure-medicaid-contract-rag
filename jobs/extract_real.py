import json

from common.azsearch import retrieve
from common.llm import ask_json
from common.verify import best_match

FIELDS = {
    "state": "US state that is party to the agreement",
    "agency_name": "the state agency name",
    "counterparty_name": "the MCO or vendor name; null if blank in the template",
    "effective_date": "start date, YYYY-MM-DD",
    "end_date": "end of the term, YYYY-MM-DD",
    "program_name": "the Medicaid program name",
    "mlr_floor_pct": "minimum medical loss ratio as a number",
    "stop_loss_limit_usd": "stop-loss limit per enrollee as a number",
    "mco_termination_deadline": "when the MCO must notify the state of intent to terminate",
}

PROMPT = """Extract the following field from the contract excerpts below.

FIELD: {field}
DEFINITION: {definition}

Return JSON with exactly these keys:
- value: the extracted value, or null if not stated
- quote: the exact sentence from the context supporting it, or null
- chunk_id: which chunk the quote came from, or null

Use ONLY the context. Do not infer.

CONTEXT:
{context}
"""

THRESHOLD = 0.85


def format_context(chunks):
    return "\n\n---\n\n".join(f"[{c['chunk_id']}] {c['text']}" for c in chunks)


def extract_field(field, definition):
    chunks = retrieve(f"{field} {definition}", top_k=5, main_only=True)
    result = ask_json(
        PROMPT.format(field=field, definition=definition, context=format_context(chunks))
    )
    return result, {c["chunk_id"]: c for c in chunks}


def check(result, by_id):
    """Verify the quote appears in the cited chunk."""
    quote, cid = result.get("quote"), result.get("chunk_id")

    if result.get("value") is None:
        return {"status": "null", "score": None}
    if not quote or not cid:
        return {"status": "uncited", "score": None}
    if cid not in by_id:
        return {"status": "bad_chunk_id", "score": 0.0}

    score = best_match(quote, by_id[cid]["text"])
    status = "verified" if score >= THRESHOLD else "unverified"
    return {"status": status, "score": round(score, 3)}


def main():
    out = {}
    counts = {}

    for field, definition in FIELDS.items():
        result, by_id = extract_field(field, definition)
        result["check"] = check(result, by_id)

        if cid := result.get("chunk_id"):
            if cid in by_id:
                result["page"] = by_id[cid]["start_page"]

        out[field] = result
        counts[result["check"]["status"]] = counts.get(result["check"]["status"], 0) + 1

        score = result["check"]["score"]
        score_str = f"{score:.2f}" if score is not None else "  - "
        page = result.get("page", "-")
        print(f"{field:28} {str(result.get('value'))[:38]:40} "
              f"{result['check']['status']:12} {score_str}  p{page}")

    with open("data/extracted_real.json", "w") as f:
        json.dump(out, f, indent=2)

    print()
    for status, n in sorted(counts.items()):
        print(f"  {status}: {n}")


if __name__ == "__main__":
    main()