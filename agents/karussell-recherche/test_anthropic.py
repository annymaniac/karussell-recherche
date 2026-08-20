"""Testet den Anthropic-API-Zugang mit einer minimalen Anfrage."""
import os

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

response = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=20,
    messages=[{"role": "user", "content": "Antworte nur mit: Verbindung erfolgreich."}],
)

print(response.content[0].text)
