from __future__ import annotations

from pathlib import Path

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.templating import Jinja2Templates

app = Starlette(debug=True)
current_dir = Path(__file__).parent
templates = Jinja2Templates(directory=str(current_dir / "templates"))


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
