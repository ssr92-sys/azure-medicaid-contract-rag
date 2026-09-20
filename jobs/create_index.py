import os

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
)

load_dotenv()

INDEX = os.environ["AZURE_SEARCH_INDEX"]

client = SearchIndexClient(
    endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
    credential=DefaultAzureCredential(),
)

fields = [
    SimpleField(name="chunk_id", type=SearchFieldDataType.String, key=True),
    SearchableField(name="text", type=SearchFieldDataType.String),
    SearchableField(name="section_path", type=SearchFieldDataType.String),
    SearchableField(name="heading", type=SearchFieldDataType.String),
    SimpleField(name="start_page", type=SearchFieldDataType.Int32, filterable=True, sortable=True),
    SimpleField(name="end_page", type=SearchFieldDataType.Int32, filterable=True),
    SimpleField(name="is_appendix", type=SearchFieldDataType.Boolean, filterable=True),
    SimpleField(name="source_file", type=SearchFieldDataType.String, filterable=True),
    SearchField(
        name="vector",
        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
        searchable=True,
        vector_search_dimensions=1536,
        vector_search_profile_name="hnsw-profile",
    ),
]

vector_search = VectorSearch(
    algorithms=[HnswAlgorithmConfiguration(name="hnsw-config")],
    profiles=[VectorSearchProfile(name="hnsw-profile", algorithm_configuration_name="hnsw-config")],
)

index = SearchIndex(name=INDEX, fields=fields, vector_search=vector_search)

client.create_or_update_index(index)
print(f"index '{INDEX}' created")