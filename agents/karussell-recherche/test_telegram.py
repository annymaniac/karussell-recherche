"""Testet den Telegram-Bot-Zugang: sendet eine Testnachricht an den konfigurierten Chat."""
import os

import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
response = requests.post(url, data={"chat_id": CHAT_ID, "text": "Test erfolgreich: Karussell-Recherche-Bot ist verbunden."})

if response.ok:
    print("Test erfolgreich: Nachricht wurde an Telegram gesendet.")
else:
    print(f"Fehler: {response.status_code} - {response.text}")
