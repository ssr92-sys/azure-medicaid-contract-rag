import os

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

from common.llm import embed

load_dotenv()

_client = SearchClient(
    endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
    index_name=os.environ["AZURE_SEARCH_INDEX"],
    credential=DefaultAzureCredential(),
)


def retrieve(query, top_k=5, main_only=False, max_page=47):
    vq = VectorizedQuery(
        vector=embed(query),
        k_nearest_neighbors=top_k * 3,
        fields="vector",
    )

    filt = None
    if main_only:
        filt = f"is_appendix eq false and start_page lt {max_page}"

    results = _client.search(
        search_text=query,
        vector_queries=[vq],
        filter=filt,
        top=top_k,
        select=["chunk_id", "text", "section_path", "heading", "start_page", "end_page"],
    )

    out = []
    for r in results:
        out.append({
            "chunk_id": r["chunk_id"],
            "text": r["text"],
            "section_path": r["section_path"],
            "heading": r["heading"],
            "start_page": r["start_page"],
            "end_page": r["end_page"],
            "score": round(r["@search.score"], 5),
        })
    return out