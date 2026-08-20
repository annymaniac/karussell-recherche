"""Formatiert analysis_result.json als Telegram-Nachricht(en) und verschickt sie.

Teilt automatisch in mehrere Nachrichten auf, falls das Telegram-Limit (4096 Zeichen) \
überschritten wird.
"""
import json
import os
from datetime import date

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(__file__)
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
TELEGRAM_LIMIT = 4096


def build_message_blocks(hits):
    today = date.today().strftime("%d.%m.%Y")
    header = f"🎠 Karussell-Recherche — {today}\n\n"

    if not hits:
        return [header + "Keine neuen, wirklich passenden Treffer diese Woche."]

    blocks = [header]
    for i, hit in enumerate(hits, 1):
        entry = (
            f"{i}. \"{hit['quote']}\"\n"
            f"📎 {hit['source_title']}\n{hit['source_url']}\n"
            f"💡 {hit['reasoning']}\n\n"
        )
        blocks.append(entry)
    return blocks


def chunk_blocks(blocks, limit=TELEGRAM_LIMIT):
    """Fasst Blöcke zu Nachrichten zusammen, ohne das Zeichenlimit zu überschreiten."""
    messages = []
    current = ""
    for block in blocks:
        if len(current) + len(block) > limit:
            if current:
                messages.append(current)
            current = block
        else:
            current += block
    if current:
        messages.append(current)
    return messages


def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    response = requests.post(url, data={"chat_id": CHAT_ID, "text": text, "disable_web_page_preview": True})
    if not response.ok:
        print(f"Fehler beim Senden: {response.status_code} - {response.text}")
    return response.ok


def main():
    result_path = os.path.join(BASE_DIR, "analysis_result.json")
    with open(result_path, encoding="utf-8") as f:
        hits = json.load(f)

    blocks = build_message_blocks(hits)
    messages = chunk_blocks(blocks)

    for i, msg in enumerate(messages, 1):
        ok = send_message(msg)
        status = "gesendet" if ok else "FEHLGESCHLAGEN"
        print(f"Nachricht {i}/{len(messages)}: {status} ({len(msg)} Zeichen)")


if __name__ == "__main__":
    main()
