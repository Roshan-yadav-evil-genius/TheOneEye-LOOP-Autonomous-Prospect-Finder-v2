from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import Request, Response

_MAX_REQUEST_ID_LENGTH = 128


async def request_id_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    incoming = request.headers.get("x-request-id", "").strip()
    request_id = incoming if 0 < len(incoming) <= _MAX_REQUEST_ID_LENGTH else str(uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response
