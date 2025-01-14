import json
from typing import Annotated

from fastapi import FastAPI, status, Request, Path
from fastapi.responses import JSONResponse
import redis

from app.models import database as db
from app.utils.base64_hash import generate_short_hash

app = FastAPI()

redis_client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)

RATE_LIMIT_WINDOW = 30  # seconds
RATE_LIMIT_COUNT = 3  # requests/window
CACHE_TTL = 300  # seconds


@app.middleware("http")
async def cache_middleware(request: Request, call_next):
    if request.url.path != "/shorten":
        return await call_next(request)

    if request.method != "GET":
        return await call_next(request)

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
    if request.url.path != "/shorten":
        return await call_next(request)

    if request.method in ["PATCH", "POST"]:
        return await call_next(request)

    unique_key = request.state.unique_key
    if redis_client.exists(unique_key):
        data = json.loads(redis_client.get(unique_key))
        data["message"] = "Already shortened."
        return JSONResponse(status_code=status.HTTP_201_CREATED,
                            content=data,
                            media_type="application/json")

    response = await call_next(request)
    return response


@app.middleware("http")
async def set_unique_key_middleware(request: Request, call_next):
    if request.url.path != "/shorten":
        return await call_next(request)

    original_url = str(request.url.path)
    if request.url.query:
        original_url += f"?{request.url.query}"

    routes = original_url.split('?')
    route, query = routes[0], routes[1].split('&')[1]

    url = f"{route}?{query}"

    key = f"{request.client.host}:{request.client.port}:{url}"
    request.state.unique_key = generate_short_hash(input_string=key)

    return await call_next(request)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path != "/shorten":
        return await call_next(request)

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
    try:
        data = db.get_entry(shortened_url)
    except Exception as e:
        print(e)
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                            content={"error": "URL not found"},
                            media_type="application/json")

    unique_key = request.state.unique_key
    redis_client.set(unique_key,
                     json.dumps(data),
                     ex=CACHE_TTL)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=data,
        media_type="application/json"
    )


@app.get("/")
async def read_redis():
    return redis_client.scan(0)
