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

# источник строки словаря, поставленной рукой (tools/dictionary.py, HAND).
# Здесь он значение данных, а не ссылка на инструмент: плагин про инструменты
# не знает и знать не должен
HAND = "рука"
DETERMINERS = {
    "der": ("der",) + EIN,
    "das": ("das",) + EIN,
    "die": ("die",) + tuple(word + "e" for word in EIN),
}


def has(sentence, part):
    """Стоит ли `part` в предложении **отдельным словом**, а не куском другого.

    Границы проверяются с обеих сторон: иначе `Tische` находилось бы по
    `Tisch`, а `keine Blume` — по `kein Blume`, и обе находки были бы про
    другую форму, то есть про другой ответ.
    """
    text, head = sentence.lower(), part.lower()
    at = text.find(head)
    while at != -1:
        after = at + len(head)
        before = text[at - 1] if at else " "
        if not before.isalpha() and (after >= len(text)
                                     or not text[after].isalpha()):
            return True
        at = text.find(head, at + 1)
    return False


def shows_word(sentence, word):
    """Стоит ли в предложении **та самая** форма, которую спрашивает карточка.

    Карточка спрашивает род `Haus`, а `Die Häuser sind alt` — предложение про
    `Häuser`. Оно верное, полезное и даже с артиклем, но слова `Haus` в нём
    нет: глаз ищет на карточке одно, а находит другое, и связка «слово —
    артикль», ради которой пример и показывают, не возникает вовсе.

    Отсюда же отбраковка `nach Hause`: дательное `-e` — другая форма, а падежей
    на этой ступени ещё не проходили, и объяснить разницу нечем.
    """
    return has(sentence, word)


def shows_gender(sentence, article, word):
    """Стоит ли слово в предложении при определителе своего рода."""
    return any(has(sentence, f"{determiner} {word}")
               for determiner in DETERMINERS[article])


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
    return any(has(sentence, f"{other} {word}")
               for other in ARTICLES if other != article)


def pick_example(view, lexeme, article, word):
    """Какой пример встанет на карточку, когда их несколько.

    Предпочтения, от старшего к младшему:

    1. **определённый артикль при слове**: `Der Führerschein ist weg` учит
       роду прямо, а `Er hat keinen Führerschein` — через склонение, которого
       на A1 ещё нет. Здесь это старше всего, включая руку: карточка
       спрашивает род, и пример, показывающий его непрозрачно, не делает
       своей работы, кем бы он ни был предложен;
    2. **рука** — пример, добавленный человеком с карточки: среди равных по
       прозрачности он старше, потому что человек смотрел, а отбор угадывает;
    3. **ein-определитель** (`ein`, `kein`, `mein`): род виден по окончанию —
       не так прямо, но виден;
    4. **короче — лучше**: длинное предложение на карточке дочитывают реже.

    Обязательного два, и они не предпочтения: в предложении стоит **та самая**
    форма, которую спрашивает карточка, и оно не врёт про род.
    """
    best = None
    for row in view.examples(lexeme):
        text = (row.get("de") or "").strip()
        if not shows_word(text, word) or misleads(text, article, word):
            continue
        rank = (0 if has(text, f"{article} {word}") else 1,
                0 if (row.get("source") or "").strip() == HAND else 1,
                0 if shows_gender(text, article, word) else 1,
                len(text))
        if best is None or rank < best[0]:
            best = (rank, text, (row.get("ru") or "").strip())
    return (best[1], best[2]) if best else ("", "")


def example_problem(card, sentence):
    """Чем предложенный пример **слабее** прочих. Пусто — годится как есть.

    Это не запрет: отбором распоряжается `pick_example`, и добавленный
    человеком пример встанет на карточку, даже если ответ здесь непустой.
    Слова эти нужны разбору правок — чтобы в журнале было видно, чем пример
    слаб, — а не для того, чтобы что-то отменить.

    Спрашивают отсюда, а не из инструмента: чем плох пример к артиклю, знает
    колода, а не разбор правок. Плагин едет обновлением контента, инструмент —
    нет, и правило, положенное не туда, чинится потом сборкой APK.

    Два требования, и они разной силы.
    **Та самая форма** — жёсткое: `Die Häuser sind alt` про `Haus` ничего не
    показывает, глаз ищет одно, а находит другое.
    **Именительный со своим артиклем** — правило A1: `Der Führerschein ist weg`
    учит роду, `Er hat keinen Führerschein` учит падежу, которого на этой
    ступени ещё нет. Косвенный определитель про род говорит, но непрозрачно:
    чтобы вывести из `keinen` мужской род, надо уже знать склонение — то есть
    пример требует знания, ради которого показан.
    """
    sentence = (sentence or "").strip()
    word, article = card["word"], card["answer"]
    if not sentence:
        return "пусто"
    if not shows_word(sentence, word):
        return f"в предложении нет формы «{word}»"
    if not has(sentence, f"{article} {word}"):
        return f"«{article} {word}» в именительном не стоит — на A1 рано"
    return ""


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


def subject(card):
    """Что стоит на экране правки: слово, как его учат, и что о нём известно.

    Называет плагин, потому что движок не знает, где в карточке слово: у
    артикля предмет правки — `das Haus`, у глагола будет ячейка парадигмы.
    Артикль здесь показан **вместе со словом**, хотя правят перевод: правка
    делается по горячим следам, и человек должен видеть ту же карточку, а не
    её половину.
    """
    return {"title": f"{card['answer']} {card['word']}",
            "accent": card["answer"],
            "note": card["translation"],
            "example": card["example"]}


def check(card, answer):
    """Разбор ответа. `feedback` строкой оставлен для старых сборок движка.

    Пример показывается **в обоих исходах**. Он не разбор ошибки, а вторая
    встреча со словом: `das Haus` в живой фразе — то, ради чего род и учат, и
    угадавшему это нужно ровно так же. Задержку он стоит; сколько её держать,
    решает движок по тому, что на экране.

    Множественное — только при промахе. Оно про **другую** клетку таблицы, и
    показывать её тому, кто первую только что назвал верно, значит добавлять
    строку на каждую карточку ради случая, когда её никто не читает.
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
    if not correct and card["plural"]:
        result["notes"].append({"text": f"{PLURAL} {card['plural']}",
                                "accent": PLURAL_ACCENT, "weight": "muted"})
    if card["example"]:
        result["notes"].append({"text": card["example"], "weight": "loud"})
    return result
