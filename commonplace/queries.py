from __future__ import annotations
from typing import *

import datetime
import logging

import edgedb


logger = logging.getLogger("commonplace.queries")


class ContentItem(Protocol):
    ts: datetime.datetime
    name: str
    title: Optional[str]
    text: str


async def get_all_tags(db: edgedb.AsyncIOConnection) -> List[str]:
    tags = await db.fetchall("SELECT DISTINCT commonplace::Content.tags;")
    return sorted(tags)


async def get_all_content(
    db: edgedb.AsyncIOConnection, tags: AbstractSet[str] = frozenset()
) -> List[ContentItem]:
    base_query = """
        WITH MODULE commonplace
        SELECT Content {
            ts := .latest.ts,
            name,
            title,
            text := .latest[IS Note].text,
            tags
        }
    """

    if len(tags) == 0:
        content = await db.fetchall(base_query + ";")
    elif len(tags) == 1:
        taglist = list(tags)
        content = await db.fetchall(
            base_query + "FILTER <Tag>$t0 IN .tags;",
            t0=taglist[0],
        )
    elif len(tags) == 2:
        taglist = list(tags)
        content = await db.fetchall(
            base_query + "FILTER <Tag>$t0 IN .tags AND <Tag>$t1 IN .tags;",
            t0=taglist[0],
            t1=taglist[1],
        )
    else:  # len(tags) > 2
        content = await db.fetchall(
            base_query + "FILTER all(array_unpack(<array<Tag>>$tags) IN .tags);",
            tags=list(tags),
        )

    return sorted(content, key=lambda o: o.ts, reverse=True)
