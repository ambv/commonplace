"""Almost one liners. But handy."""

from __future__ import annotations
from typing import *

import datetime
import hashlib
from pathlib import Path
import random
import string

import dateutil.tz


def find_dot_env(directory: Path) -> Optional[Path]:
    if not directory.is_dir():
        return None

    while True:
        maybe_result = directory / ".env"
        if maybe_result.is_file():
            return maybe_result

        if directory.root == directory:
            # we are at the root, we failed
            return None

        directory = directory.parent


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


def random_string(length: int) -> str:
    return "".join(
        random.choice(string.ascii_letters + string.digits)
        for _ in range(length)
    )


def nowtz() -> datetime.datetime:
    return datetime.datetime.now(tz=dateutil.tz.tzlocal())


def sha1(arg: Union[str, bytes]) -> bytes:
    hash = hashlib.sha1()
    if isinstance(arg, str):
        arg = arg.encode("utf8")
    hash.update(arg)
    return hash.digest()
