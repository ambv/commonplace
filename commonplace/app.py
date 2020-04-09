from __future__ import annotations
from typing import *

import logging
from pathlib import Path

import edgedb

from starlette.applications import Starlette
from starlette.config import Config
from starlette.datastructures import URL, Secret
from starlette.requests import Request
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from commonplace.convenience import find_dot_env

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
