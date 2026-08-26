"""Режим «Формы глаголов»: показан инфинитив и местоимение, надо ввести форму.

Умляуты можно вводить как ae/oe/ue/ss: "du faehrst" засчитается как "du fährst".
"""

PLUGIN = "verbs"

# id карточки — `курс:лексема:признак:направление` (tools/cardid.py, Р-10).
# Время в признаке выписано, а не подразумевается: появится Präteritum — он
# добавит новые id и не тронет ни одного существующего.
COURSE = "de"

TENSE = "praes"  # в колоде пока только презенс; Präteritum придёт колонкой

# местоимение в CSV — это подпись на экране, а в id идёт лицо с числом.
# «sie» и «Sie» сюда не вписаны нарочно: у них форма 3-го лица множественного,
# и решать, одна это карточка или две, надо в тот момент, когда они появятся в
# колоде, — а не задним числом обнаружить, что они склеились.
PERSON = {"ich": "1sg", "du": "2sg", "er": "3sg", "er/sie/es": "3sg",
          "wir": "1pl", "ihr": "2pl"}


# для сборки из словаря нужна обратная карта: у ячейки местоимение одно, хотя
# у местоимения ячейка не одна («er», «sie», «es» — все praes.3sg). Какое из
# них показывать — решение колоды, а не словаря
PRONOUN = {"1sg": "ich", "2sg": "du", "3sg": "er",
           "1pl": "wir", "2pl": "ihr"}


def build(view):
    """Карточки этой колоды из словаря (tools/build_deck.py).

    По карточке на ячейку парадигмы, и только на те ячейки, которые открыты
    набором: на A1 это презенс, а `ginge` подождёт своего уровня.
    """
    for lexeme in view.lexemes:
        row = view.row(lexeme)
        if (row.get("pos") or "").strip() != "verb":
            continue
        translation = view.sense(lexeme)
        for person, pronoun in PRONOUN.items():
            feature = f"{TENSE}.{person}"
            if not view.allows(feature):
                continue
            form = view.form(lexeme, feature)
            if not form:
                continue
            yield {"lexeme": lexeme, "infinitive": (row.get("lemma") or "").strip(),
                   "pronoun": pronoun, "form": form, "translation": translation}


def id_parts(row):
    """(лексема, признак, направление); None — строка на карточку не годится."""
    person = PERSON.get((row.get("pronoun") or "").strip())
    if not person:
        return None
    return (row.get("lexeme") or "").strip(), f"{TENSE}.{person}", "produce"


# запасной ключ для CSV без колонки id: пара «лексема + местоимение».
# Сама форма — это ответ, её правка не должна обнулять прогресс
ID_FIELDS = ["lexeme", "pronoun"]

# откуда импортёр берёт лемму (tools/import_deck.py): у глагола это инфинитив,
# а не форма — формы разных лиц принадлежат одной лексеме
LEMMA_FIELD = "infinitive"
LEXEME_POS = "verb"

DECKS = [
    {
        "id": "de-verbs",
        "title": "Формы глаголов (Präsens)",
        "data": "data/de_verbs.csv",
    },
]


def make_card(row):
    infinitive = (row.get("infinitive") or "").strip()
    pronoun = (row.get("pronoun") or "").strip()
    form = (row.get("form") or "").strip()
    if not infinitive or not pronoun or not form:
        return None
    return {
        "infinitive": infinitive,
        "pronoun": pronoun,
        "form": form,
        "translation": (row.get("translation") or "").strip(),
    }


def render(card):
    hint = f" — {card['translation']}" if card["translation"] else ""
    return {
        "prompt": f"{card['infinitive']}{hint}\n{card['pronoun']} ___",
        "input": {"type": "text"},
    }


def check(card, answer):
    return {
        "correct": _norm(answer) == _norm(card["form"]),
        "feedback": f"{card['pronoun']} {card['form']}",
    }


def _norm(s):
    s = s.strip().lower()
    for umlaut, ascii_ in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        s = s.replace(umlaut, ascii_)
    return s
