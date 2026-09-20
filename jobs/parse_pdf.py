import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient

load_dotenv()

OUT = "data/md_healthchoice_2026.md"

if os.path.exists(OUT):
    print(f"{OUT} already exists — skipping (delete it to re-parse)")
    raise SystemExit

client = DocumentIntelligenceClient(
    endpoint=os.environ["AZURE_DOCINTEL_ENDPOINT"],
    credential=DefaultAzureCredential(),
)

with open("data/raw/md_healthchoice_2026.pdf", "rb") as f:
    poller = client.begin_analyze_document(
        "prebuilt-layout",
        body=f,
        output_content_format="markdown",
    )

result = poller.result()

with open(OUT, "w") as f:
    f.write(result.content)

print(f"wrote {OUT} ({len(result.content):,} chars)")