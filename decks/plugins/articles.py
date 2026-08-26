"""Режим «Артикли»: показывается существительное, надо выбрать der/die/das."""

PLUGIN = "articles"

DECKS = [
    {
        "id": "de-articles",
        "title": "Артикли (der / die / das)",
        "data": "data/de_nouns.csv",
    },
]

# id карточки — `курс:лексема:признак:направление` (tools/cardid.py, Р-10).
# Признака нет: спрашивается род самой лексемы, а не одна из её форм, поэтому
# третий сегмент — `_`. Направление `genus` — то, что реально спрашивается.
COURSE = "de"


def id_parts(row):
    """(лексема, признак, направление) — из чего собран id этой строки.

    Лексема берётся ссылкой из колонки `lexeme`, а не из написания: `der See`
    и `die See` пишутся одинаково, а карточки это разные, и развести их можно
    только разными id лексем в data/lexemes.csv.
    """
    return (row.get("lexeme") or "").strip(), None, "genus"


# запасной ключ для CSV без колонки id (чужие таблицы, Google Sheets):
# ссылка на лексему, а не написание — по той же причине
ID_FIELDS = ["lexeme"]

# откуда импортёр берёт лемму, когда чужая таблица ссылок на лексемы не знает
# (tools/import_deck.py). Здесь, а не ключом командной строки: какая колонка
# несёт слово — свойство колоды, и повторять его в каждом запуске значит
# однажды повторить неверно.
LEMMA_FIELD = "noun"
LEXEME_POS = "noun"

ARTICLES = ("der", "die", "das")

# артикль не хранится, а выводится: род — свойство лексемы, и держать рядом с
# ним ещё и артикль значило бы держать одно и то же дважды
GENUS = {"m": "der", "f": "die", "n": "das"}


def build(view):
    """Карточки этой колоды из словаря (tools/build_deck.py).

    Существительное без рода пропускается молча: у `Eltern` и `Leute` его нет
    вовсе, они бывают только во множественном, и артикль у них спрашивать
    нечего. Это не пробел в данных, а свойство слова.
    """
    for lexeme in view.lexemes:
        row = view.row(lexeme)
        if (row.get("pos") or "").strip() != "noun":
            continue
        article = GENUS.get((row.get("gender") or "").strip())
        if not article or not view.allows(None):
            continue
        yield {"lexeme": lexeme, "noun": (row.get("lemma") or "").strip(),
               "article": article, "translation": view.sense(lexeme)}


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
