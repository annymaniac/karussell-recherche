"""Analysiert gesammelte Kommentare mit Claude und liefert kuratierte Content-Treffer.

Nutzt research_memory.json, damit sich Treffer über mehrere Wochen nicht wiederholen.
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

RANKING_PROMPT = """Du analysierst YouTube-Kommentare für Anna-Maria Leuzzi, die leistungsfähige, \
reflektierte Frauen begleitet, die rational wissen was sie tun müssten, es aber in der \
entscheidenden Situation trotzdem nicht umsetzen (Selbstsabotage, innere Muster, Identität).

Ranking-Logik, in dieser Reihenfolge:
1. MUSTERRELEVANZ (harter Filter, nicht nur Gewichtung): Der Kommentar zählt nur, wenn er das \
Muster "ich weiß, was ich tun müsste - und tue es trotzdem nicht" widerspiegelt. Generische \
Aussagen wie "toller Content" oder unspezifisches "ich fühl mich unsicher" zählen NICHT.
2. WIEDERHOLUNG: Ähnliche Formulierungen/Fragen, die bei mehreren Kommentaren auftauchen, sind \
wertvoller als Einzelfälle.
3. SPRACHLICHE SCHÄRFE: Bevorzuge konkrete, zitierfähige Formulierungen, die fast 1:1 als Hook \
oder Caption-Zeile nutzbar wären.

NICHT als Kriterium: Like-Anzahl/Popularität.

Dir werden ggf. bereits in früheren Läufen verwendete Zitate/Themen mitgegeben - schlage diese \
NICHT nochmal vor, auch nicht in leicht abgewandelter Form. Wenn ein neuer Kommentar inhaltlich \
dasselbe sagt wie ein bereits verwendetes Zitat, zählt er nicht als neuer Treffer.

Geh die Kommentare durch und denk laut nach, welche das Muster wirklich treffen (kurz, pro \
Kandidat 1-2 Sätze Begründung). Maximal 10 Treffer, ruhig auch weniger - erfinde nichts und \
fülle nicht künstlich auf.

Schließe deine Antwort IMMER mit einem JSON-Codeblock ab, der deine finale Auswahl enthält \
(auch wenn die Auswahl leer ist), exakt in diesem Format:

```json
[{"quote": "Original-Zitat wortwörtlich", "source_title": "Video-Titel", "source_url": "URL", \
"reasoning": "ein Satz, warum es passt"}]
```"""


def load_memory():
    if not os.path.exists(MEMORY_PATH):
        return []
    with open(MEMORY_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_memory(memory):
    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


def main():
    raw_path = os.path.join(BASE_DIR, "raw_comments.json")
    with open(raw_path, encoding="utf-8") as f:
        videos = json.load(f)

    comment_blocks = []
    for video in videos:
        for c in video["comments"]:
            comment_blocks.append(
                f'[Video: "{video["video_title"]}" | {video["video_url"]}]\n{c["text"]}'
            )
    corpus = "\n\n---\n\n".join(comment_blocks)

    memory = load_memory()
    if memory:
        used_quotes = "\n".join(f'- "{entry["quote"]}"' for entry in memory)
        user_content = (
            f"Bereits in früheren Läufen verwendete Zitate (nicht wiederholen):\n{used_quotes}\n\n"
            f"Hier sind die neu gesammelten Kommentare:\n\n{corpus}"
        )
    else:
        user_content = f"Hier sind die gesammelten Kommentare:\n\n{corpus}"

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        system=RANKING_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )

    result_text = response.content[0].text.strip()

    if "```json" not in result_text:
        print("Fehler: Kein JSON-Block in der Antwort gefunden. Rohtext:")
        print(result_text)
        return
    json_block = result_text.split("```json", 1)[1].split("```", 1)[0].strip()
    try:
        hits = json.loads(json_block)
    except json.JSONDecodeError:
        print("Fehler: JSON-Block war nicht valide. Rohtext:")
        print(json_block)
        return

    today = date.today().isoformat()
    for hit in hits:
        hit["date"] = today
    memory.extend(hits)
    save_memory(memory)

    json_out_path = os.path.join(BASE_DIR, "analysis_result.json")
    with open(json_out_path, "w", encoding="utf-8") as f:
        json.dump(hits, f, ensure_ascii=False, indent=2)

    md_lines = [f"# Karussell-Recherche — {today}\n"]
    if not hits:
        md_lines.append("Keine neuen, wirklich passenden Treffer diese Woche.")
    for i, hit in enumerate(hits, 1):
        md_lines.append(f"## {i}. \"{hit['quote']}\"\n")
        md_lines.append(f"**Quelle:** {hit['source_title']} | {hit['source_url']}\n")
        md_lines.append(f"**Warum es passt:** {hit['reasoning']}\n")
    md_text = "\n".join(md_lines)

    md_out_path = os.path.join(BASE_DIR, "analysis_result.md")
    with open(md_out_path, "w", encoding="utf-8") as f:
        f.write(md_text)

    print(md_text)
    print(f"\n\n{len(hits)} neue Treffer. Gespeichert in: {md_out_path}")
    print(f"Research Memory jetzt: {len(memory)} Einträge insgesamt.")


if __name__ == "__main__":
    main()
