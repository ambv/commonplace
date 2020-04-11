from __future__ import annotations
from typing import *

import asyncio
import logging
import datetime
import random

import click
import edgedb

from . import app
from .convenience import lorem_ipsum, nowtz, random_string, sha1


logger = logging.getLogger("commonplace.db_boostrap")
logger.setLevel(logging.DEBUG if app.debug else logging.INFO)


full_dsn = f"edgedb://{app.db_user}:{app.db_password}@{app.db_host}/{app.db_db}"
no_db_dsn = f"edgedb://{app.db_user}:{app.db_password}@{app.db_host}/edgedb"
no_user_dsn = f"edgedb://edgedb@{app.db_host}/edgedb"


async def try_connect() -> Tuple[edgedb.AsyncIOConnection, str]:
    try:
        return (await edgedb.async_connect(full_dsn)), full_dsn
    except edgedb.AuthenticationError as ae:
        logger.warning(f"Full DSN doesn't work: {ae}")

    try:
        return (await edgedb.async_connect(no_db_dsn)), no_db_dsn
    except edgedb.AuthenticationError as ae:
        logger.warning(f"No DB DSN doesn't work: {ae}")

    try:
        return (await edgedb.async_connect(no_user_dsn)), no_user_dsn
    except edgedb.AuthenticationError as ae:
        logger.warning(f"No user DSN doesn't work: {ae}")

    raise LookupError("No way to connect to the given database found.")


async def update_schema(db: edgedb.AsyncIOConnection) -> AsyncGenerator[str, None]:
    yield "Updating DB schema"
    esdl = app.current_dir.parent / "database.esdl"
    if not esdl.is_file():
        raise LookupError("database.esdl not found")

    schema = esdl.read_text()
    async with db.transaction():
        yield "Creating migration"
        await db.execute(f"CREATE MIGRATION setupdb TO {{ {schema} }};")
        yield "Committing migration"
        await db.execute(f"COMMIT MIGRATION setupdb;")

    yield "Done updating schema"


async def bootstrap() -> AsyncGenerator[str, None]:
    conn, dsn = await try_connect()
    if dsn == no_user_dsn:
        yield f"User {app.db_user} does not exist, creating"
        await conn.execute(
            f"""
            CREATE SUPERUSER ROLE {app.db_user} {{
                SET password := {app.db_password}
            }}
            """
        )
        await conn.aclose()
        conn, dsn = await try_connect()
        if dsn == no_user_dsn:
            raise ValueError(f"Logging with created role {app.db_user} does not work")

    if dsn == no_db_dsn:
        yield f"Connected to EdgeDB as {app.db_user}, creating database {app.db_db}"
        # TODO: uncomment when passwords work with RDS
        # await conn.execute("CONFIGURE SYSTEM RESET Auth FILTER Auth.method IS Trust;")
        await conn.execute(f"CREATE DATABASE {app.db_db}")
        await conn.aclose()
        conn, dsn = await try_connect()

    if dsn != full_dsn:
        raise ValueError(f"Opening database {app.db_db} does not work")

    yield (
        f"Connected to database {app.db_db} as {app.db_user},"
        f" migrating schema to latest ESDL"
    )

    async for message in update_schema(conn):
        yield message

    yield "Done bootstrapping"


async def make_test_data(
    db: Optional[edgedb.AsyncIOConnection] = None,
) -> AsyncGenerator[str, None]:
    if db is None:
        db, dsn = await try_connect()
        if dsn != full_dsn:
            raise ValueError(
                f"Opening database {app.db_db} does not work. Bootstrap first?"
            )

    typenames = await db.fetchall(
        """
        SELECT schema::ObjectType { name }
        FILTER .name LIKE 'commonplace::%'
        AND .is_abstract = false;
        """
    )
    for typeobj in typenames:
        typename = typeobj.name
        yield f"Deleting {typename} objects"
        await db.execute(f"DELETE {typename}")

    yield "Done making test data"


async def drop_test_data(
    db: Optional[edgedb.AsyncIOConnection] = None,
) -> AsyncGenerator[str, None]:
    if db is None:
        db, dsn = await try_connect()
        if dsn != full_dsn:
            raise ValueError(
                f"Opening database {app.db_db} does not work. Bootstrap first?"
            )

    yield "Populating test data"
    usernames = ["ambv", "1st1", "elprans"]
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
        yield f"Inserting user {user}"
        await db.fetchall(
            """
            WITH MODULE commonplace
            INSERT User { name := <Slug>$name };
            """,
            name=user,
        )
    content_count = 100
    for i in range(1, content_count + 1):
        yield f"{i}/{content_count}: inserting note"
        text = " ".join(lorem_ipsum(random.randint(3, 20)))
        editor_name = random.choice(usernames)
        seconds = random.randint(0, seconds_in_3_years)
        seconds = random.randint(0, seconds)
        seconds = random.randint(0, seconds)
        ts = nowtz() - datetime.timedelta(seconds=seconds)
        note = await db.fetchone(
            """
            WITH MODULE commonplace
            INSERT Note {
                text := <str>$text,
                sha1 := <bytes>$hash,
                ts := <datetime>$ts,
                editor := (
                    SELECT User FILTER User.name = <Slug>$name
                )
            }
            """,
            text=text,
            hash=sha1(text),
            ts=ts,
            name=editor_name,
        )

        content_title = None
        if random.random() > 0.8:
            content_title = " ".join(lorem_ipsum(5))
        content_name = "-".join(random_string(8) for _ in range(3)).lower()
        public_toss = random.random()
        public_since: Optional[datetime.datetime]
        public_until: Optional[datetime.datetime]
        if public_toss < 0.2:
            public_since = nowtz() - datetime.timedelta(seconds=seconds)
            public_until = nowtz()
        elif public_toss < 0.4:
            public_since = nowtz() + datetime.timedelta(seconds=seconds)
            public_until = None
        elif public_toss > 0.5:
            public_since = None
            public_until = None

        yield f"{i}/{content_count}: inserting content"
        await db.fetchone(
            """
            WITH MODULE commonplace
            INSERT Content {
                latest := (
                    SELECT Note FILTER Note.id = <uuid>$noteid
                ),
                title := <str>$title,
                name := <Slug>$name,
                tags := <array<Tag>>$tags,
                public_since := <datetime>$public_since,
                public_until := <datetime>$public_until,
                deleted := <bool>$deleted
            }
            """,
            noteid=note.id,
            title=content_title,
            name=content_name,
            tags=random.sample(tags, random.randint(0, len(tags))),
            public_since=public_since,
            public_until=public_until,
            deleted=False if random.random() > 0.1 else True,
        )

    yield "Done dropping test data"


async def log(agen: AsyncGenerator[str, None]) -> None:
    async for message in agen:
        logger.info(message)


@click.command()
@click.option(
    "--bootstrap",
    "operation",
    flag_value="bootstrap",
    default=True,
    help=(
        f"Bootstrap EdgeDB at {app.db_host} to include user {app.db_user},"
        f" database {app.db_db}, and an up-to-date schema from database.esdl"
    ),
)
@click.option(
    "--make-test-data",
    "operation",
    flag_value="make-test-data",
    help=f"Writes random test data to edgedb://{app.db_host}/{app.db_db}",
)
@click.option(
    "--drop-test-data",
    "operation",
    flag_value="drop-test-data",
    help=f"Deletes all data from edgedb://{app.db_host}/{app.db_db}",
)
def main(operation: str) -> None:
    logging.basicConfig()
    if operation == "bootstrap":
        agen = bootstrap()
    elif operation == "make-test-data":
        agen = make_test_data()
    elif operation == "drop-test-data":
        agen = drop_test_data()
    else:
        raise click.UsageError(f"Unknown action {operation}")

    asyncio.run(log(agen))


if __name__ == "__main__":
    main()
