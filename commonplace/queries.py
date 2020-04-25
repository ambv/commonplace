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
    tags: List[str]


async def get_all_tags(pool: edgedb.AsyncIOPool) -> List[Tuple[str, bool]]:
    async with pool.acquire() as db:
        return await _get_all_tags(db)


async def get_all_content(
    pool: edgedb.AsyncIOPool, tags: AbstractSet[str] = frozenset()
) -> List[ContentItem]:
    async with pool.acquire() as db:
        return await _get_all_content(db, tags)


async def _get_all_tags(db: edgedb.AsyncIOConnection) -> List[Tuple[str, bool]]:
    """Return a sorted list of 2-tuples like: ("tag name", bool("tag name" in seen))."""

    return sorted(await db.fetchall("SELECT DISTINCT commonplace::Content.tags;"))


async def _get_all_content(
    db: edgedb.AsyncIOConnection, tags: AbstractSet[str] = frozenset()
) -> List[ContentItem]:
    """Return a sorted list of ContentItem-like objects that contain `tags`."""

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
            base_query + "FILTER <Tag>$t0 IN .tags;", t0=taglist[0],
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
