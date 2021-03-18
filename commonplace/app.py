from __future__ import annotations

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response

app = Starlette(debug=True)


@app.route("/error")
async def error(request: Request) -> Response:
    raise RuntimeError("Oh no")


@app.exception_handler(404)
async def not_found(request: Request, exc: Exception) -> Response:
    return Response(b"not found")
