from fastapi import FastAPI, status, HTTPException, Header, Request
from fastapi.responses import JSONResponse
import redis

from app.models import database as db

app = FastAPI()

redis_client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)

RATE_LIMIT_WINDOW = 5  # seconds
RATE_LIMIT_COUNT = 5  # requests/second


@app.post("/shorten")
async def shorten_url(
    request: Request,
    url: str,
    shortened_url: str | None = None,
    idempotency_key: str = Header(...)
):
    cached_response = redis_client.hgetall(idempotency_key)
    if cached_response is not None:
        return JSONResponse(status_code=status.HTTP_201_CREATED,
                            content=cached_response,
                            media_type="application/json")

    shorten: dict = db.create_new_entry(url, shortened_url)

    redis_client.hset(idempotency_key, shorten)
    redis_client.hexpire(idempotency_key, RATE_LIMIT_WINDOW)

    return JSONResponse(status_code=status.HTTP_201_CREATED, content=shorten, media_type="application/json")
