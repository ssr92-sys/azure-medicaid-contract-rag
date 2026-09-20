# Azure Medicaid Contract RAG

RAG pipeline over 400+ page Medicaid managed care contracts. Built on Azure OpenAI,
Document Intelligence, and AI Search, deployed as an API on Azure Functions.

## What it does

Ingests a state Medicaid managed care agreement (tested on Maryland's CY2026
HealthChoice MCO Agreement — 410 pages, 20 appendices), and answers natural-language
questions about it with citations traceable to a specific clause and page.

## Pipeline

PDF → Document Intelligence (layout model, markdown output)
    → structure-aware chunking with section hierarchy + page provenance
    → embeddings (text-embedding-3-small)
    → Azure AI Search index
    → hybrid retrieval (vector + BM25, RRF fusion, metadata filtering)
    → grounded answer with citations
    → automated citation verification


## Notable design decisions

**Structure-aware chunking.** The document contains a HIPAA Business Associate
Agreement with its own termination clause, and four separate "Definitions" sections.
Chunks carry their full heading trail so these are distinguishable.

**Two-signal appendix detection.** Document Intelligence's heading levels are
unreliable, so appendix classification is derived from page number rather than
section path.

**Citation verification.** Quoted text is fuzzy-matched against the cited chunk.
Elided quotes are split on ellipsis and each fragment verified separately, so
legitimate abbreviated quotes pass while fabrications fail.

**No API keys.** Entra ID managed identity and RBAC throughout, locally and deployed.

## Layout

- `common/` — LLM client, chunking, retrieval (local + Azure), verification
- `jobs/` — ingestion and query scripts
- `api/` — Azure Functions app

## Evaluation

- Synthetic ground truth: generate contracts from known facts, extract, compare
- Retrieval: recall@1, recall@5, MRR against a labelled question set
- Hallucination: citation verification on every generated answer
