from __future__ import annotations
from typing import *

import logging
from pathlib import Path

import edgedb

from starlette.applications import Starlette
from starlette.config import Config
from starlette.datastructures import URL, Secret
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from commonplace.convenience import find_dot_env, nowtz, sha1

current_dir = Path(__file__).parent
config = Config(find_dot_env(current_dir))

debug = config("COMMONPLACE_DEBUG", cast=bool, default=False)
db_host = config("EDGEDB_HOST")
db_user = config("EDGEDB_USER")
db_password = config("EDGEDB_PASSWORD", cast=Secret)
db_db = config("EDGEDB_DB", default="commonplace")
db_dsn = URL(f"edgedb://{db_user}:{db_password}@{db_host}/{db_db}")
db_pool: edgedb.AsyncIOPool
templates = Jinja2Templates(directory=str(current_dir / "templates"))
logger = logging.getLogger()
logger.setLevel(logging.DEBUG if debug else logging.INFO)


app = Starlette(debug=debug)
app.mount("/static", StaticFiles(directory=str(current_dir / "static")), name="static")


@app.on_event("startup")
async def startup() -> None:
    global db_pool
    logger.info("Creating an async connection pool to EdgeDB")
    db_pool = await edgedb.create_async_pool(dsn=str(db_dsn), min_size=1, max_size=16)


@app.on_event("shutdown")
async def shutdown() -> None:
    await db_pool.aclose()


@app.route("/")
async def homepage(request: Request) -> Response:
    async with db_pool.acquire() as db:
        await db.execute("select 1;")
        template = "index.html"
        context = {"request": request}
        return templates.TemplateResponse(template, context)


@app.route("/error")
async def error(request: Request) -> Response:
    """
    An example error. Switch the `debug` setting to see either tracebacks or 500 pages.
    """
    raise RuntimeError("Oh no")


@app.exception_handler(404)
async def not_found(request: Request, exc: Exception) -> Response:
    """
    Return an HTTP 404 page.
    """
    template = "404.html"
    context = {"request": request}
    return templates.TemplateResponse(template, context, status_code=404)


@app.exception_handler(500)
async def server_error(request: Request, exc: Exception) -> Response:
    """
    Return an HTTP 500 page.
    """
    template = "500.html"
    context = {"request": request, "exception": exc}
    return templates.TemplateResponse(template, context, status_code=500)


if db_db == "cptest":
    import datetime
    import random
    from commonplace.convenience import lorem_ipsum, random_string

    def log(msg: str) -> str:
        logger.info(msg, stacklevel=2)
        return msg + "\n"

    @app.route("/update-schema")
    async def update_schema(request: Request) -> StreamingResponse:
        async def stream() -> AsyncGenerator[str, None]:
            yield log("Updating DB schema")
            esdl = current_dir.parent / "database.esdl"
            if not esdl.is_file():
                raise LookupError("database.esdl not found")

            schema = esdl.read_text()
            async with db_pool.acquire() as db:
                async with db.transaction():
                    yield log("Creating migration")
                    await db.execute(f"CREATE MIGRATION setupdb TO {{ {schema} }};")
                    yield log("Committing migration")
                    await db.execute(f"COMMIT MIGRATION setupdb;")

            yield log("Done")

        return StreamingResponse(stream(), media_type="text/plain")

    @app.route("/clear-test-data")
    async def clear_test_data(request: Request) -> StreamingResponse:
        async def stream() -> AsyncGenerator[str, None]:
            async with db_pool.acquire() as db:
                typenames = await db.fetchall(
                    """
                    SELECT schema::ObjectType { name }
                    FILTER .name LIKE 'commonplace::%'
                    AND .is_abstract = false;
                    """
                )
                for typeobj in typenames:
                    typename = typeobj.name
                    yield log(f"Deleting {typename} objects")
                    await db.execute(f"DELETE {typename}")

            yield log("Done")
        return StreamingResponse(stream(), media_type="text/plain")

    @app.route("/make-test-data")
    async def make_test_data(request: Request) -> StreamingResponse:
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

        async def stream() -> AsyncGenerator[str, None]:
            yield log("Populating test data")
            async with db_pool.acquire() as db:
                for user in usernames:
                    yield log(f"Inserting user {user}")
                    await db.fetchall(
                        """
                        WITH MODULE commonplace
                        INSERT User { name := <Slug>$name };
                        """,
                        name=user,
                    )
                content_count = 100
                for i in range(1, content_count + 1):
                    yield log(f"{i}/{content_count}: inserting note")
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

                    yield log(f"{i}/{content_count}: inserting content")
                    await db.fetchone(
                        """
                        WITH MODULE commonplace
                        INSERT Content {
                            latest := (
                                SELECT Note FILTER Note.id = <uuid>$noteid
                            ),
                            title := <str>$title,
                            name := <Slug>$name,
                            tags := <array<str>>$tags,
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

                    yield log("Done")

        return StreamingResponse(stream(), media_type="text/plain")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
