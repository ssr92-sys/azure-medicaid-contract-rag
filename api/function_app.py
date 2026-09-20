import json
import logging
import time

import azure.functions as func

from common.azsearch import retrieve
from common.llm import ask
from common.verify import verify

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

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
    return "\n\n---\n\n".join(
        f"[{c['chunk_id']}] (page {c['start_page']}, {c['section_path']})\n{c['text']}"
        for c in chunks
    )


def error(message, status, **extra):
    body = {"error": message, **extra}
    return func.HttpResponse(
        json.dumps(body), status_code=status, mimetype="application/json"
    )


@app.route(route="ask", methods=["POST"])
def ask_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
    except ValueError:
        return error("body must be JSON", 400)

    question = body.get("question")
    if not question or not isinstance(question, str):
        return error("missing or invalid 'question'", 400)
    if len(question) > 1000:
        return error("question too long (max 1000 chars)", 400)

    main_only = bool(body.get("main_only", True))
    top_k = max(1, min(int(body.get("top_k", 5)), 20))

    t0 = time.perf_counter()

    try:
        chunks = retrieve(question, top_k=top_k, main_only=main_only)
        t_retrieval = time.perf_counter() - t0

        t1 = time.perf_counter()
        answer = ask(PROMPT.format(context=format_context(chunks), question=question))
        t_generation = time.perf_counter() - t1

        checks = verify(answer, chunks)
        all_verified = all(c["verified"] for c in checks) if checks else None
        total_ms = round((time.perf_counter() - t0) * 1000)

        logging.info(
            "rag_query_complete",
            extra={"custom_dimensions": {
                "question_length": len(question),
                "main_only": main_only,
                "top_k": top_k,
                "chunks_returned": len(chunks),
                "top_score": chunks[0]["score"] if chunks else 0,
                "answer_length": len(answer),
                "quotes_checked": len(checks),
                "all_verified": all_verified,
                "retrieval_ms": round(t_retrieval * 1000),
                "generation_ms": round(t_generation * 1000),
                "total_ms": total_ms,
            }},
        )

        payload = {
            "question": question,
            "answer": answer,
            "citations": [
                {
                    "chunk_id": c["chunk_id"],
                    "page": c["start_page"],
                    "section": c["section_path"],
                    "score": c["score"],
                }
                for c in chunks
            ],
            "verification": checks,
            "all_quotes_verified": all_verified,
            "timing_ms": {
                "retrieval": round(t_retrieval * 1000),
                "generation": round(t_generation * 1000),
                "total": total_ms,
            },
        }

        return func.HttpResponse(
            json.dumps(payload), status_code=200, mimetype="application/json"
        )

    except Exception as e:
        logging.exception(
            "rag_query_failed",
            extra={"custom_dimensions": {
                "error_type": type(e).__name__,
                "question_length": len(question),
                "elapsed_ms": round((time.perf_counter() - t0) * 1000),
            }},
        )
        return error(type(e).__name__, 500, detail=str(e))


@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({"status": "ok"}), status_code=200, mimetype="application/json"
    )