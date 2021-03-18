from __future__ import annotations

from pathlib import Path

import edgedb
import logging

from starlette.applications import Starlette
from starlette.config import Config
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

current_dir = Path(__file__).parent
config = Config(current_dir / ".env")
debug = config("COMMONPLACE_DEBUG", cast=bool, default=False)
db_instance = config("COMMONPLACE_DB", default="commonplace")
db_pool: edgedb.AsyncIOPool
templates = Jinja2Templates(directory=str(current_dir / "templates"))
app = Starlette(debug=debug)
app.mount("/static", StaticFiles(directory=str(current_dir / "static")), name="static")
logger = logging.getLogger("commonplace.app")
logger.setLevel(logging.DEBUG if debug else logging.INFO)


@app.on_event("startup")
async def startup() -> None:
    global db_pool
    db_pool = await edgedb.create_async_pool(db_instance, min_size=1, max_size=16)
    logger.info("Created the connection pool to EdgeDB")


@app.on_event("shutdown")
async def shutdown() -> None:
    await db_pool.aclose()
    logger.info("Closed the connection pool to EdgeDB")


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
        context={"request": request, "domain": "lukasz.langa.pl", "title": "404!"},
        status_code=404,
    )


@app.exception_handler(500)
async def internal_server_error(request: Request, exc: Exception) -> Response:
    return templates.TemplateResponse(
        name="500.html",
        context={"request": request, "domain": "lukasz.langa.pl", "title": "500!"},
        status_code=500,
    )
