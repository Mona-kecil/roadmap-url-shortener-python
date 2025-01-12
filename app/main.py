import json

from fastapi import FastAPI, status, HTTPException, Header, Request
from fastapi.responses import JSONResponse
import redis

from app.models import database as db

app = FastAPI()

redis_client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)

RATE_LIMIT_WINDOW = 30  # seconds
RATE_LIMIT_COUNT = 3  # requests/window


@app.post("/shorten")
async def shorten_url(
    request: Request,
    url: str,
    shortened_url: str | None = None,
    idempotency_key: str = Header(...)
):
    cached_response = redis_client.get(idempotency_key)
    if cached_response is not None:
        return JSONResponse(status_code=status.HTTP_201_CREATED,
                            content=json.loads(cached_response),
                            media_type="application/json")

    client_id = f"{request.client.host}:{request.client.port}"
    key = f"rate_limit:{client_id}"

    request_count = redis_client.get(key)

    if request_count is None:
        redis_client.set(key, 1, ex=RATE_LIMIT_WINDOW)
    else:
        request_count = int(request_count)
        if request_count >= RATE_LIMIT_COUNT:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Try again later."
            )
        else:
            redis_client.incr(key)

    shorten: dict = db.create_new_entry(url, shortened_url)
    cache = shorten.copy()
    cache["type"] = "cache"

    redis_client.set(idempotency_key, json.dumps(
        cache), ex=RATE_LIMIT_WINDOW)

    return JSONResponse(status_code=status.HTTP_201_CREATED, content=shorten, media_type="application/json")


@app.get('/')
def test_get_client(request: Request):
    return JSONResponse(status_code=status.HTTP_200_OK, content=f"{request.client.host}:{request.client.port}")
