"""Режим «Артикли»: показывается существительное, надо выбрать der/die/das."""

PLUGIN = "articles"

DECKS = [
    {
        "id": "de-articles",
        "title": "Артикли (der / die / das)",
        "data": "data/de_nouns.csv",
    },
]

# чем карточки отличаются друг от друга, если в CSV нет колонки id.
# Артикль сюда не входит намеренно: это ответ, и его исправление не должно
# считаться появлением новой карточки. Омонимы (der See / die See) разводятся
# явным id в CSV — см. tools/gen_ids.py.
ID_FIELDS = ["noun"]

ARTICLES = ("der", "die", "das")


def make_card(row):
    word = (row.get("noun") or "").strip()
    article = (row.get("article") or "").strip().lower()
    if not word or article not in ARTICLES:
        return None  # битые строки в таблице молча пропускаем
    return {
        "word": word,
        "answer": article,
        "translation": (row.get("translation") or "").strip(),
    }


def render(card):
    return {
        "prompt": card["word"],
        "input": {"type": "choices", "options": list(ARTICLES)},
    }


def check(card, answer):
    feedback = f"{card['answer']} {card['word']}"
    if card["translation"]:
        feedback += f" — {card['translation']}"
    return {
        "correct": answer.strip().lower() == card["answer"],
        "feedback": feedback,
    }
