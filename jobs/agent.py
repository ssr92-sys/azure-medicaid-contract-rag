import json
import sys

from common.azsearch import retrieve
from common.llm import ask_with_tools
from common.verify import verify

SYSTEM = """You answer questions about a Medicaid managed care contract.

Use the search_contract tool to find relevant passages. You may call it more
than once with different queries or scopes if the question needs it.

Answer ONLY from tool results. If the answer isn't there, say so.
Cite chunks in square brackets, like [md2026-0040]. Quote exact contract language.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_contract",
            "description": (
                "Search the contract for relevant passages. "
                "The main agreement is pages 1-47; appendices (including the HIPAA "
                "Business Associate Agreement and COMAR regulations) are pages 48-410."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What to search for",
                    },
                    "scope": {
                        "type": "string",
                        "enum": ["main_agreement", "everything"],
                        "description": "main_agreement excludes appendices",
                    },
                },
                "required": ["query", "scope"],
            },
        },
    }
]

_seen = {}


def search_contract(query, scope):
    chunks = retrieve(query, top_k=5, main_only=(scope == "main_agreement"))
    for c in chunks:
        _seen[c["chunk_id"]] = c
    return [
        {
            "chunk_id": c["chunk_id"],
            "page": c["start_page"],
            "section": c["section_path"],
            "text": c["text"][:3000],
        }
        for c in chunks
    ]


def main():
    question = sys.argv[1] if len(sys.argv) > 1 else \
        "How does the termination clause in the main agreement differ from the one in the HIPAA appendix?"

    _seen.clear()
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": question},
    ]

    answer, history = ask_with_tools(
        messages, TOOLS, {"search_contract": search_contract}
    )

    answer += ' The contract also states "the MCO shall provide free parking to all enrollees." [md2026-0040]'


    print(f"Q: {question}\n")

    print("--- tool calls ---")
    for m in history:
        if isinstance(m, dict) and m.get("tool_calls"):
            for tc in m["tool_calls"]:
                args = json.loads(tc["function"]["arguments"])
                print(f"  search_contract({args})")
    print()

    print(answer)

    checks = verify(answer, list(_seen.values()))
    if checks:
        print("\n--- citation check ---")
        for r in checks:
            mark = "OK  " if r["verified"] else "FAIL"
            print(f"  {mark} {r['score']:.2f}  {r['chunk_id']}  \"{r['quote'][:55]}...\"")


if __name__ == "__main__":
    main()