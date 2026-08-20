"""Destilliert aus research_memory.json die dahinterliegenden 'brennenden Fragen'.

Pflegt fragen_archiv.json - ein wachsendes Archiv, das NIE geleert oder auf eine feste \
Zahl begrenzt wird. Jede Woche kommen neue Fragen aus neuen Zitaten dazu. Anna-Maria \
markiert Fragen als bearbeitet, sobald sie daraus Content (Karussell/Talking-Head/Story) \
gemacht hat - offene Fragen bleiben im Archiv sichtbar, bis sie bearbeitet sind.
"""
import json
import os
from datetime import date

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

BASE_DIR = os.path.dirname(__file__)
MEMORY_PATH = os.path.join(BASE_DIR, "research_memory.json")
FRAGEN_PATH = os.path.join(BASE_DIR, "fragen_archiv.json")

DISTILL_PROMPT = """Du destillierst aus Zitaten (YouTube-Kommentare, Forum-Posts) die dahinterliegende \
"brennende Frage" - die Frage, die sich die Person eigentlich stellt, formuliert so, wie \
Anna-Maria Leuzzi (Identitäts-Architektin, Muster erkennen -> innere Logik verstehen -> \
Veränderung ermöglichen) sie in einem Talking-Head-Reel, Karussell-Post oder einer Story \
beantworten würde.

Die Frage muss:
- Direkt aus dem Zitat ableitbar sein, nichts dazuerfinden
- Das Muster treffen: "ich weiß, was ich tun müsste - und tue es trotzdem nicht"
- Kurz und zitierfähig sein, wie eine Frage, die man als Hook nutzen könnte

Gib für jedes Zitat ein Objekt zurück. Schließe deine Antwort IMMER mit einem \
JSON-Codeblock ab, exakt in diesem Format:

```json
[{"quelle_zitat": "identisches Zitat wie im Input", "frage": "Die destillierte Frage"}]
```"""


def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    memory = load_json(MEMORY_PATH)
    fragen = load_json(FRAGEN_PATH)

    already_processed = {f["quelle_zitat"] for f in fragen}
    new_entries = [m for m in memory if m["quote"] not in already_processed]

    if not new_entries:
        print("Keine neuen Zitate zu destillieren. Fragen-Archiv unverändert.")
        return

    quotes_block = "\n\n".join(f'- "{e["quote"]}"' for e in new_entries)

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        system=DISTILL_PROMPT,
        messages=[{"role": "user", "content": f"Zitate:\n\n{quotes_block}"}],
    )

    result_text = response.content[0].text.strip()
    if "```json" not in result_text:
        print("Fehler: Kein JSON-Block in der Antwort gefunden.")
        print(result_text)
        return
    json_block = result_text.split("```json", 1)[1].split("```", 1)[0].strip()
    try:
        distilled = json.loads(json_block)
    except json.JSONDecodeError:
        print("Fehler: JSON-Block war nicht valide.")
        print(json_block)
        return

    entries_by_quote = {e["quote"]: e for e in new_entries}
    today = date.today().isoformat()
    added = 0
    for d in distilled:
        source = entries_by_quote.get(d.get("quelle_zitat"))
        if not source:
            continue
        fragen.append({
            "frage": d["frage"],
            "quelle_zitat": source["quote"],
            "quelle_titel": source["source_title"],
            "quelle_url": source["source_url"],
            "datum": source.get("date", today),
            "bearbeitet": False,
        })
        added += 1

    save_json(FRAGEN_PATH, fragen)
    offen = sum(1 for f in fragen if not f["bearbeitet"])
    print(f"{added} neue Fragen destilliert. Fragen-Archiv: {len(fragen)} gesamt, {offen} offen (unbearbeitet).")


if __name__ == "__main__":
    main()
