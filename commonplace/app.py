from __future__ import annotations

import logging
from pathlib import Path

import edgedb
from starlette.applications import Starlette
from starlette.config import Config
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response, StreamingResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from . import convenience

current_dir = Path(__file__).parent
config = Config(current_dir / ".env")
debug = config("COMMONPLACE_DEBUG", cast=bool, default=False)
db_instance = config("COMMONPLACE_DB", default="commonplace")
db_pool: edgedb.AsyncIOClient
templates = Jinja2Templates(directory=str(current_dir / "templates"))
app = Starlette(debug=debug)
app.mount("/static", StaticFiles(directory=str(current_dir / "static")), name="static")
logger = logging.getLogger("commonplace.app")
logger.setLevel(logging.DEBUG if debug else logging.INFO)


@app.on_event("startup")
async def startup() -> None:
    global db_pool
    db_pool = edgedb.create_async_client(db_instance, max_concurrency=16)
    await db_pool.ensure_connected()
    logger.info("Created the connection pool to EdgeDB")
    templates.env.globals.update(
        {
            "domain": "lukasz.langa.pl",
            "make_tags_query": convenience.make_tags_query,
            "humanize_dt": convenience.get_english_dt_description_from_now,
            "icon_class": convenience.icon_class,
        }
    )


@app.on_event("shutdown")
async def shutdown() -> None:
    await db_pool.aclose()
    logger.info("Closed the connection pool to EdgeDB")


@app.route("/")
async def homepage(request: Request) -> Response:
    query_tags = frozenset(request.query_params.getlist("t"))

    content = await convenience.query_content(db_pool, query_tags)
    tags = await db_pool.query("SELECT DISTINCT commonplace::Content.tags;")
    available_tags = {tag for item in content for tag in item.tags}
    tags_with_availability = ((tag, tag in available_tags) for tag in tags)

    return templates.TemplateResponse(
        name="index.html",
        context={
            "request": request,
            "title": "Łukasz Langa",
            "content": content,
            "tags": tags_with_availability,
            "query_tags": query_tags,
        },
    )


@app.route("/favicon.ico")
async def favicon(request: Request) -> Response:
    return RedirectResponse(url="/static/favicon32.png")


@app.route("/error")
async def error(request: Request) -> Response:
    raise RuntimeError("Oh no")


@app.exception_handler(404)
async def not_found(request: Request, exc: Exception) -> Response:
    return templates.TemplateResponse(
        name="404.html",
        context={"request": request, "title": "404!"},
        status_code=404,
    )


@app.exception_handler(500)
async def internal_server_error(request: Request, exc: Exception) -> Response:
    return templates.TemplateResponse(
        name="500.html",
        context={"request": request, "title": "500!"},
        status_code=500,
    )


if debug:

    @app.route("/drop-data")
    async def drop_test_data(request: Request) -> StreamingResponse:
        return StreamingResponse(
            convenience.drop_test_data(db_pool), media_type="text/plain"
        )

    @app.route("/make-data")
    async def make_test_data(request: Request) -> StreamingResponse:
        return StreamingResponse(
            convenience.make_test_data(db_pool), media_type="text/plain"
        )
