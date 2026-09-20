import sys

from common.llm import ask
from common.azsearch import retrieve
from common.verify import verify

PROMPT = """You are answering questions about a Medicaid managed care contract.

Answer using ONLY the context below. If the answer is not in the context, say
"Not found in the provided context."

After each fact, cite the chunk it came from in square brackets, like [md2026-0040].
Quote the exact contract language where possible.

CONTEXT:
{context}

QUESTION: {question}
"""


def format_context(chunks):
    parts = []
    for c in chunks:
        parts.append(
            f"[{c['chunk_id']}] (page {c['start_page']}, {c['section_path']})\n{c['text']}"
        )
    return "\n\n---\n\n".join(parts)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main_only = "--main-only" in sys.argv
    question = args[0] if args else "When does this agreement terminate?"

    chunks = retrieve(question, top_k=5, main_only=main_only)
    answer = ask(PROMPT.format(context=format_context(chunks), question=question))

    print(f"Q: {question}\n")
    print(answer)

    print("\n--- sources ---")
    for c in chunks:
        print(f"  {c['chunk_id']}  p{c['start_page']}  {c['section_path'][:60]}")

    checks = verify(answer, chunks)
    if checks:
        print("\n--- citation check ---")
        for r in checks:
            mark = "OK  " if r["verified"] else "FAIL"
            print(f"  {mark} {r['score']:.2f}  {r['chunk_id']}  \"{r['quote'][:60]}...\"")


if __name__ == "__main__":
    main()