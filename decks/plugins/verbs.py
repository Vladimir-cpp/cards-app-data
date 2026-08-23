"""Режим «Формы глаголов»: показан инфинитив и местоимение, надо ввести форму.

Умляуты можно вводить как ae/oe/ue/ss: "du faehrst" засчитается как "du fährst".
"""

PLUGIN = "verbs"

# карточку задаёт пара «инфинитив + местоимение»; сама форма — это ответ,
# её правка не должна обнулять прогресс
ID_FIELDS = ["infinitive", "pronoun"]

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
