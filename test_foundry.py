
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

endpoint = os.getenv("FOUNDRY_ENDPOINT")
api_key = os.getenv("FOUNDRY_API_KEY")
model = os.getenv("FOUNDRY_MODEL", "gpt-4.1-mini")

if not endpoint or not api_key:
    raise ValueError(
        "FOUNDRY_ENDPOINT or FOUNDRY_API_KEY is missing from .env"
    )

client = OpenAI(
    base_url=endpoint,
    api_key=api_key,
)

response = client.responses.create(
    model=model,
    input="Reply with exactly: AgriSense AI connection successful."
)

print(response.output_text)
