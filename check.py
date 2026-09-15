import os
from dotenv import load_dotenv

load_dotenv()

print(os.environ.get("AZURE_OPENAI_ENDPOINT"))
print(os.environ.get("AZURE_OPENAI_DEPLOYMENT"))