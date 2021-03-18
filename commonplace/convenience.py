from __future__ import annotations

import datetime
import random
import string
from typing import AsyncGenerator, Iterator

import dateutil.tz
import edgedb


def random_string(length: int) -> str:
    return "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(length)
    )


def lorem_ipsum(count: int) -> Iterator[str]:
    sentence_start = True
    for _ in range(count):
        word = random.choice(lorem_ipsum_words)
        if sentence_start:
            sentence_start = False
            word = word.capitalize()
        if random.random() > 0.8:
            word += random.choice(".....!!?")
            sentence_start = True
        yield word


def get_english_timedelta_description(delta: datetime.timedelta) -> str:
    days = delta.days + delta.seconds / 3600 / 24
    hours = delta.seconds / 3600
    minutes = delta.seconds % 3600 / 60
    seconds = delta.seconds % 3600 % 60

    if days > 0.5:
        if 0.9 < days < 1:
            days = 0.9
        unit = "day" if days == 1 else "days"
        return f"{days:.0f} {unit}" if days == int(days) else f"{days:.1f} {unit}"
    elif hours > 0.5:
        if 0.9 < hours < 1:
            hours = 0.9
        unit = "hour" if hours == 1 else "hours"
        if hours == int(hours):
            return f"{hours:.0f} {unit}"
        return f"{hours:.1f} {unit}"
    elif minutes > 0.5:
        if 0.9 < minutes < 1:
            minutes = 0.9
        unit = "minute" if minutes == 1 else "minutes"
        if minutes == int(minutes):
            return f"{minutes:.0f} {unit}"
        return f"{minutes:.1f} {unit}"
    else:
        unit = "second" if seconds == 1 else "seconds"
        return f"{seconds} {unit}"


def get_english_dt_description_from_now(ts: datetime.datetime) -> str:
    delta = nowtz() - ts
    return get_english_timedelta_description(delta)


def nowtz() -> datetime.datetime:
    return datetime.datetime.now(tz=dateutil.tz.tzlocal())  # type: ignore


def icon_class(tag: str) -> str:
    cls = _icon_classes.get(tag.lower(), "")
    if not cls and tag.endswith("s"):
        cls = _icon_classes.get(tag.lower()[:-1], "")
    return "uil-" + (cls or "angle-right")


async def drop_test_data(db: edgedb.AsyncIOPool) -> AsyncGenerator[str, None]:
    yield "Dropping all data from database\n"
    typenames = await db.query(
        """
        SELECT schema::ObjectType { name }
        FILTER .name LIKE 'commonplace::%'
        AND .is_abstract = false;
        """
    )
    retry = True
    while retry:
        retry = False
        for typeobj in typenames:
            typename = typeobj.name
            yield f"Deleting {typename} objects\n"
            try:
                await db.query(f"DELETE {typename}")
            except edgedb.ConstraintViolationError:
                retry = True

    yield "Done dropping test data\n"


async def make_test_data(db: edgedb.AsyncIOPool) -> AsyncGenerator[str, None]:
    yield "Populating test data\n"
    usernames = ["ambv", "yury", "elprans"]
    tags = [
        "articles",
        "bookmarks",
        "fiction",
        "guitar",
        "inspirations",
        "journal",
        "learning",
        "philosophy",
        "python",
        "quotes",
    ]
    seconds_in_3_years = 60 * 60 * 24 * 365 * 3

    for user in usernames:
        yield f"Inserting user {user}\n"
        try:
            await db.query(
                """
                WITH MODULE commonplace
                INSERT User { name := <util::Slug>$name };
                """,
                name=user,
            )
        except edgedb.ExecutionError as ee:
            yield f"ERROR: {str(ee)}\n"

    content_count = 100
    for i in range(1, content_count + 1):
        yield f"{i}/{content_count}: inserting note\n"
        text = " ".join(lorem_ipsum(random.randint(3, 20)))
        content_title = None
        if random.random() > 0.8:
            content_title = " ".join(lorem_ipsum(5))
        content_name = "-".join(random_string(8) for _ in range(3)).lower()
        seconds = random.randint(0, seconds_in_3_years)
        seconds = random.randint(0, seconds)
        seconds = random.randint(0, seconds)
        public_toss = random.random()
        public_since: datetime.datetime | None
        public_until: datetime.datetime | None
        if public_toss < 0.25:
            public_since = nowtz() - datetime.timedelta(seconds=seconds)
            public_until = nowtz()
        elif public_toss < 0.5:
            public_since = nowtz() + datetime.timedelta(seconds=seconds)
            public_until = None
        elif public_toss >= 0.5:
            public_since = None
            public_until = None
        try:
            await db.query(
                """
                WITH MODULE commonplace
                INSERT Note {
                    title := <OPTIONAL str>$title,
                    name := <util::Slug>$name,
                    text := <str>$text,
                    tags := array_unpack(<array<util::Tag>>$tags),
                    public_since := <OPTIONAL datetime>$public_since,
                    public_until := <OPTIONAL datetime>$public_until,
                    deleted := <bool>$deleted
                }
                """,
                title=content_title,
                name=content_name,
                text=text,
                tags=random.sample(tags, random.randint(0, len(tags))),
                public_since=public_since,
                public_until=public_until,
                deleted=False if random.random() > 0.1 else True,
            )
        except edgedb.ExecutionError as ee:
            yield f"ERROR: {str(ee)}\n"

    yield "Done making test data\n"


lorem_ipsum_words = [
    "ad",
    "adipiscing",
    "aliqua",
    "aliquip",
    "amet",
    "anim",
    "aute",
    "cillum",
    "commodo",
    "consectetur",
    "consequat",
    "culpa",
    "cupidatat",
    "deserunt",
    "do",
    "dolor",
    "dolore",
    "duis",
    "ea",
    "eiusmod",
    "elit",
    "enim",
    "esse",
    "est",
    "et",
    "eu",
    "ex",
    "excepteur",
    "exercitation",
    "fugiat",
    "id",
    "in",
    "incididunt",
    "ipsum",
    "irure",
    "labore",
    "laboris",
    "laborum",
    "lorem",
    "magna",
    "minim",
    "mollit",
    "nisi",
    "non",
    "nostrud",
    "nulla",
    "occaecat",
    "officia",
    "pariatur",
    "proident",
    "qui",
    "quis",
    "reprehenderit",
    "sed",
    "sint",
    "sit",
    "sunt",
    "tempor",
    "ullamco",
    "ut",
    "velit",
    "veniam",
    "voluptate",
]

# Those are mapped to uil-* classes in https://github.com/iconscout/unicons/
_icon_classes = {
    "anger": "angry",
    "award": "medal",
    "article": "notes",
    "book": "book-open",
    "bookmark": "bookmark",
    "car": "car",
    "challenger": "car",
    "company": "chart-line",
    "conference": "meeting-board",
    "database": "database",
    "design": "ruler",
    "diary": "diary",
    "drawing": "pen",
    "edgedb": "database",
    "experiment": "flask-potion",
    "favorite": "star",
    "favourite": "star",
    "fiction": "pen",
    "film": "film",
    "finance": "money-stack",
    "free-will": "wind",
    "future": "mountains-sun",
    "game": "table-tennis",
    "growth": "arrow-growth",
    "guitar": "music",
    "haiku": "pen",
    "happiness": "smile-dizzy",
    "health": "medkit",
    "home": "home",
    "house": "home",
    "humor": "smile-beam",
    "inspiration": "lightbulb-alt",
    "interpretation": "comment-question",
    "joy": "smile-squint-wink",
    "learning": "graduation-cap",
    "lightbulb": "lightbulb-alt",
    "lyric": "microphone",
    "medal": "medal",
    "megaphone": "megaphone",
    "money": "money-stack",
    "montypython": "smile-wink-alt",
    "monty-python": "smile-wink-alt",
    "motivation": "game-structure",
    "movie": "film",
    "music": "music",
    "negotiation": "ninja",
    "ninja": "ninja",
    "notes": "notes",
    "journal": "diary",
    "opensource": "code-branch",
    "open-source": "code-branch",
    "paiting": "brush-alt",
    "philosophy": "map-marker-question",
    "podcast": "microphone",
    "poetry": "pen",
    "presentation": "presentation-play",
    "procrastination": "squint",
    "programming": "bug",
    "project": "code-branch",
    "publishing": "megaphone",
    "python": "parking-circle",
    "reason": "comment-question",
    "receipt": "receipt",
    "reflection": "thunderstorm-sun",
    "question": "question-circle",
    "quote": "align-left-justify",
    "recognition": "medal",
    "singing": "microphone",
    "speaking": "megaphone",
    "talk": "megaphone",
    "tracking": "monitor-heart-rate",
    "travel": "desert",
    "weltschmerz": "thunderstorm",
    "work": "constructor",
    "writing": "pen",
}
