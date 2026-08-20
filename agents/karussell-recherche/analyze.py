"""Analysiert gesammelte Kommentare mit Claude und liefert kuratierte Content-Treffer."""
import json
import os

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

RANKING_PROMPT = """Du analysierst YouTube-Kommentare für Anna-Maria Leuzzi, die leistungsfähige, \
reflektierte Frauen begleitet, die rational wissen was sie tun müssten, es aber in der \
entscheidenden Situation trotzdem nicht umsetzen (Selbstsabotage, innere Muster, Identität).

Ranking-Logik, in dieser Reihenfolge:
1. MUSTERRELEVANZ (härter Filter, nicht nur Gewichtung): Der Kommentar zählt nur, wenn er das \
Muster "ich weiß, was ich tun müsste - und tue es trotzdem nicht" widerspiegelt. Generische \
Aussagen wie "toller Content" oder unspezifisches "ich fühl mich unsicher" zählen NICHT.
2. WIEDERHOLUNG: Ähnliche Formulierungen/Fragen, die bei mehreren Kommentaren auftauchen, sind \
wertvoller als Einzelfälle.
3. SPRACHLICHE SCHÄRFE: Bevorzuge konkrete, zitierfähige Formulierungen, die fast 1:1 als Hook \
oder Caption-Zeile nutzbar wären.

NICHT als Kriterium: Like-Anzahl/Popularität.

Gib die 5-10 besten Treffer zurück. Für jeden Treffer:
- Das Original-Zitat (wortwörtlich)
- Quelle (Video-Titel + URL)
- Ein Satz, warum es passt

Falls unter den Kommentaren keine 5 wirklich passenden Treffer sind, gib weniger zurück - \
erfinde nichts und fülle nicht künstlich auf."""


def main():
    raw_path = os.path.join(os.path.dirname(__file__), "raw_comments.json")
    with open(raw_path, encoding="utf-8") as f:
        videos = json.load(f)

    comment_blocks = []
    for video in videos:
        for c in video["comments"]:
            comment_blocks.append(
                f'[Video: "{video["video_title"]}" | {video["video_url"]}]\n{c["text"]}'
            )

    corpus = "\n\n---\n\n".join(comment_blocks)

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2000,
        system=RANKING_PROMPT,
        messages=[{"role": "user", "content": f"Hier sind die gesammelten Kommentare:\n\n{corpus}"}],
    )

    result_text = response.content[0].text
    print(result_text)

    out_path = os.path.join(os.path.dirname(__file__), "analysis_result.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result_text)
    print(f"\n\nGespeichert in: {out_path}")


if __name__ == "__main__":
    main()
