import json
import hashlib
import base64
from typing import Annotated

from fastapi import FastAPI, status, Request, Path
from fastapi.responses import JSONResponse
import redis

from app.models import database as db

app = FastAPI()

redis_client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)

RATE_LIMIT_WINDOW = 30  # seconds
RATE_LIMIT_COUNT = 3  # requests/window
CACHE_TTL = 300  # seconds


def generate_short_hash(*, input_string: str, length: int = 5) -> str:
    """
    Generate a SHA256 hash of the input string and encode it in base64
    truncating it to the desired length.
    """
    hash_obj = hashlib.sha256(input_string.encode())
    base64_hash = base64.urlsafe_b64encode(hash_obj.digest()).decode()
    return base64_hash[:length]


@app.middleware("http")
async def cache_middleware(request: Request, call_next):
    unique_key = request.state.unique_key
    if unique_key is None:
        return await call_next(request)

    cached_response = redis_client.get(unique_key)
    if cached_response is not None:
        data: dict = json.loads(cached_response)
        data['type'] = "cache"
        print('fetch data from cache')
        return JSONResponse(status_code=status.HTTP_201_CREATED,
                            content=data,
                            media_type="application/json")

    response = await call_next(request)
    return response


@app.middleware("http")
async def idempotency_middleware(request: Request, call_next):
    original_url = str(request.url.path)
    if request.url.query:
        original_url += f"?{request.url.query}"

    urls = original_url.split('?')
    queries = urls[0].split('&')
    print(urls)
    print(queries)

    key = f"{request.client.host}:{request.client.port}:{original_url}"
    print(key)

    unique_key = generate_short_hash(input_string=key)
    if redis_client.exists(unique_key):
        data = json.loads(redis_client.get(unique_key))
        data["message"] = "Already shortened."
        return JSONResponse(status_code=status.HTTP_201_CREATED,
                            content=data,
                            media_type="application/json")
    request.state.unique_key = unique_key
    response = await call_next(request)
    return response


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_id = f"{request.client.host}:{request.client.port}"
    key = f"rate_limit:{client_id}"

    if redis_client.exists(key):
        request_count = int(redis_client.get(key))
    else:
        redis_client.set(key, 0, ex=RATE_LIMIT_WINDOW)
        request_count = 0

    if request_count >= RATE_LIMIT_COUNT:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content="Rate limit exceeded. Try again later."
        )

    redis_client.incr(key)

    response = await call_next(request)
    return response


@app.post("/shorten")
async def shorten_url(
    request: Request,
    url: str,
    shortened_url: str | None = None,
):
    try:
        shorten: dict = db.create_new_entry(url, shortened_url)
    except Exception as e:
        print(e)
        return JSONResponse(status_code=status.HTTP_409_CONFLICT,
                            content={"message": "Failed to shorten URL. Shortened URL already used."})

    unique_key = request.state.unique_key
    redis_client.set(unique_key,
                     json.dumps(shorten),
                     ex=CACHE_TTL)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=shorten,
        media_type="application/json"
    )


@app.get("/shorten/{shortened_url}")
async def read_url(
    request: Request,
    shortened_url: Annotated[str, Path(title="Shortened URL")]
):
    data = db.get_entry(shortened_url)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=data,
        media_type="application/json"
    )


@app.get("/")
async def read_redis():
    return redis_client.scan(0)
