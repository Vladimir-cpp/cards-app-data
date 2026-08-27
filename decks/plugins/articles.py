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

# какие задания делает этот плагин: по нему набор решает, вычеркнуто ли
# слово именно отсюда. «Привет» не спрашивают на род, но учат как слово
DIRECTION = "genus"


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

# во множественном артикль всегда один, каким бы ни был род. Роль цвета у
# него при этом **своя** (`plural`), а не `die`: в учебной раскладке
# множественное — четвёртая клетка таблицы, жёлтая, и `die Häuser` красным
# сказало бы «женский род», чего про `Haus` не говорят
PLURAL = "die"
PLURAL_ACCENT = "plural"

# артикль не хранится, а выводится: род — свойство лексемы, и держать рядом с
# ним ещё и артикль значило бы держать одно и то же дважды
GENUS = {"m": "der", "f": "die", "n": "das"}


# Определители ein-склонения: `ein Tisch`, `mein Tisch`, но `eine Blume`,
# `meine Blume`. Окончание `-e` есть только у женского, поэтому предложение с
# ними про род всё-таки говорит — не так прямо, как `der Tisch`, но говорит.
EIN = ("ein", "kein", "mein", "dein", "sein", "ihr", "unser", "euer")
DETERMINERS = {
    "der": ("der",) + EIN,
    "das": ("das",) + EIN,
    "die": ("die",) + tuple(word + "e" for word in EIN),
}


def shows_gender(sentence, article, word):
    """Стоит ли слово в предложении при определителе своего рода."""
    text = sentence.lower()
    for determiner in DETERMINERS[article]:
        head = f"{determiner} {word}".lower()
        at = text.find(head)
        while at != -1:
            after = at + len(head)
            before = text[at - 1] if at else " "
            # `keine Blume` не должна находиться по `kein Blume`, а `Tische`
            # по `Tisch`: границы слова проверяются с обеих сторон
            if not before.isalpha() and (after >= len(text)
                                         or not text[after].isalpha()):
                return True
            at = text.find(head, at + 1)
    return False


def misleads(sentence, article, word):
    """Стоит ли слово при **чужом** определённом артикле.

    Отбраковывается и **правильный** немецкий, и это не перестраховка.
    `Ich suche die Schlüssel` — верное предложение с множественным; `an der
    Anmeldung` — верный дательный женского рода. Но карточка спрашивает
    `der/die/das` и учит **ассоциацией**: рядом со словом окажется чужой
    артикль, и запомнится он, а падежей на этой ступени ещё не проходили.
    Такой пример хуже, чем никакого, поэтому в запасные он не идёт.

    Именно поэтому проверка смотрит на форму, а не на падеж: разбирать падеж
    незачем, если результат один — пример не годится.
    """
    text = sentence.lower()
    for other in ARTICLES:
        if other == article:
            continue
        head = f"{other} {word}".lower()
        at = text.find(head)
        while at != -1:
            after = at + len(head)
            before = text[at - 1] if at else " "
            if not before.isalpha() and (after >= len(text)
                                         or not text[after].isalpha()):
                return True
            at = text.find(head, at + 1)
    return False


def pick_example(view, lexeme, article, word):
    """Предложение, где слово стоит **при определителе**, — иначе оно не про род.

    У `Haus` первым в списке идёт `Wir müssen nach Hause`. Предложение хорошее
    и по полосе i+1 отобрано верно, но артикля в нём нет вовсе, а карточка ровно
    про артикль. Поэтому сначала ищется тот пример, где род видно; и лишь если
    такого нет — самый короткий: длинное предложение на карточке не читают, а
    пропускают.

    Порядок отбора по сложности, сделанный при импорте, этим не отменяется —
    он и задаёт список, из которого здесь выбирают.
    """
    rows = view.examples(lexeme)
    if not rows:
        return "", ""
    for row in rows:
        if shows_gender(row.get("de") or "", article, word):
            return (row.get("de") or "").strip(), (row.get("ru") or "").strip()
    plain = [row for row in rows if not misleads(row.get("de") or "",
                                                 article, word)]
    if not plain:
        return "", ""
    short = min(plain, key=lambda row: len(row.get("de") or ""))
    return (short.get("de") or "").strip(), (short.get("ru") or "").strip()


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
        word = (row.get("lemma") or "").strip()
        example, example_ru = pick_example(view, lexeme, article, word)
        # множественное хранится голой формой: `die` перед ним — не данные, а
        # правило немецкого, и знает его плагин, а не таблица
        yield {"lexeme": lexeme, "noun": word,
               "article": article, "translation": view.sense(lexeme),
               "plural": view.form(lexeme, "pl"),
               "example": example, "example_ru": example_ru}


def make_card(row):
    word = (row.get("noun") or "").strip()
    article = (row.get("article") or "").strip().lower()
    if not word or article not in ARTICLES:
        return None  # битые строки в таблице молча пропускаем
    return {
        "word": word,
        "answer": article,
        "translation": (row.get("translation") or "").strip(),
        "plural": (row.get("plural") or "").strip(),
        "example": (row.get("example") or "").strip(),
    }


def render(card):
    """Вопрос: перевод подсказкой, слово вопросом, три артикля вариантами.

    `accents` — **роли**, а не цвета: плагин называет то, что знает про язык
    (какого рода вариант), палитра остаётся в движке. Плагин, назначающий
    цвета сам, — это второе приложение внутри первого.

    `options` остаются строками нарочно. Контент едет на телефон отдельно от
    APK, и список словарей положил бы установленную сборку насмерть; лишний
    ключ рядом она просто не заметит.
    """
    return {
        "hint": card["translation"],
        "prompt": card["word"],
        # место слева от слова, которое движок занимает заранее: после ответа
        # туда встанет артикль, и строка не должна от этого сдвинуться. Какой
        # из вариантов шире, знает плагин, а не движок
        "reserve": max(ARTICLES, key=len),
        "input": {
            "type": "choices",
            "options": list(ARTICLES),
            "accents": {article: article for article in ARTICLES},
        },
    }


def check(card, answer):
    """Разбор ответа. `feedback` строкой оставлен для старых сборок движка.

    Множественное и пример показываются **только при промахе**. При верном
    ответе они пролетят непрочитанными, а задерживать верный ответ значит
    наказывать за него. Решает это плагин, а не движок: что стоит показать
    ошибшемуся — вопрос обучения, а не рисования.
    """
    article, word = card["answer"], card["word"]
    correct = answer.strip().lower() == article
    feedback = f"{article} {word}"
    if card["translation"]:
        feedback += f" — {card['translation']}"
    result = {
        "correct": correct,
        "answer": article,
        "accent": article,
        "reveal": {"lead": article, "text": word},
        "feedback": feedback,
        "notes": [],
    }
    if not correct:
        if card["plural"]:
            result["notes"].append({"text": f"{PLURAL} {card['plural']}",
                                    "accent": PLURAL_ACCENT,
                                    "weight": "muted"})
        if card["example"]:
            result["notes"].append({"text": card["example"], "weight": "loud"})
    return result
