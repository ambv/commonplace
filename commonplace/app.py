from __future__ import annotations

from pathlib import Path

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

current_dir = Path(__file__).parent
templates = Jinja2Templates(directory=str(current_dir / "templates"))
app = Starlette(debug=True)
app.mount("/static", StaticFiles(directory=str(current_dir / "static")), name="static")


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
