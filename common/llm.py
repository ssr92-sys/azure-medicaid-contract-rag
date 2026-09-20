import json
import os

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI

load_dotenv()

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(),
    "https://cognitiveservices.azure.com/.default",
)

client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    azure_ad_token_provider=token_provider,
    api_version="2024-10-21",
    timeout=60.0,
    max_retries=2,
)

DEPLOYMENT = os.environ["AZURE_OPENAI_DEPLOYMENT"]


def ask(prompt):
    resp = client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


def ask_json(prompt):
    resp = client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)


EMBED_DEPLOYMENT = os.environ["AZURE_OPENAI_EMBED_DEPLOYMENT"]


def embed(text):
    resp = client.embeddings.create(
        model=EMBED_DEPLOYMENT,
        input=text,
    )
    return resp.data[0].embedding


def ask_with_tools(messages, tools, tool_functions, max_turns=5):
    """Run a tool-calling loop until the model returns a final answer."""
    for _ in range(max_turns):
        resp = client.chat.completions.create(
            model=DEPLOYMENT,
            messages=messages,
            tools=tools,
        )
        msg = resp.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls:
            return msg.content, messages

        for call in msg.tool_calls:
            fn = tool_functions[call.function.name]
            args = json.loads(call.function.arguments)
            result = fn(**args)
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result),
            })

    return "max turns exceeded", messages