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
    tags = await db.fetchall("SELECT DISTINCT array_unpack(commonplace::Content.tags);")
    return sorted(tags)


async def get_all_content(db: edgedb.AsyncIOConnection) -> List[ContentItem]:
    content = await db.fetchall(
        """
        SELECT commonplace::Content {
            ts := .latest.ts,
            name,
            title,
            text := .latest[IS commonplace::Note].text,
            tags
        };
        """
    )
    return sorted(content, key=lambda o: o.ts, reverse=True)
