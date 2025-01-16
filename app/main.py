import json
from typing import Annotated
from datetime import datetime

from fastapi import FastAPI, status, Request, Path
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis

from app.models import database as db
from app.utils.base64_hash import generate_short_hash

app = FastAPI()

redis_client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)

RATE_LIMIT_WINDOW = 30  # seconds
RATE_LIMIT_COUNT = 3  # requests/window
CACHE_TTL = 300  # seconds


class URL(BaseModel):
    id: int
    original_url: str
    shortened_url: str
    created_at: datetime
    updated_at: datetime | None
    deleted_at: datetime | None


class URLStats(URL):
    views: int


@app.middleware("http")
async def cache_middleware(request: Request, call_next):
    if not request.url.path.startswith("/shorten"):
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

        if request.url.path.__contains__("/shorten/"):
            return RedirectResponse(status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                                    url=data['original_url'])

        return JSONResponse(status_code=status.HTTP_201_CREATED,
                            content=data,
                            media_type="application/json")

    response = await call_next(request)
    return response


@app.middleware("http")
async def idempotency_middleware(request: Request, call_next):
    if not request.url.path.startswith("/shorten"):
        return await call_next(request)

    if request.method not in ["PATCH", "POST"]:
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
    if not request.url.path.startswith("/shorten"):
        return await call_next(request)

    original_url = str(request.url.path)
    if request.url.query:
        original_url += f"?{request.url.query}"

    if request.url.path.__contains__("/shorten/"):
        routes = original_url.split('/')
        route, query = routes[1:3]
    else:
        routes = original_url.split('?')
        queries = routes[1].split('&')
        route, query = routes[0], queries[1]

    url = f"{route}?{query}"

    key = f"{request.client.host}:{request.client.port}:{url}"

    unique_key = generate_short_hash(input_string=key)
    request.state.unique_key = unique_key

    return await call_next(request)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if not request.url.path.startswith("/shorten"):
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


app.add_middleware(CORSMiddleware,
                   allow_origins=["*"],
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"])


@app.post("/shorten")
async def shorten_url(
    request: Request,
    url: str,
    shortened_url: str | None = None,
):
    try:
        shorten: URL = db.create_new_entry(url, shortened_url)
    except Exception as e:
        print(e)
        return JSONResponse(status_code=status.HTTP_409_CONFLICT,
                            content={"message": "Failed to shorten URL. Shortened URL already used."})
    try:
        unique_key = request.state.unique_key
    except Exception as e:
        print(e)
        print(request.state)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": "Internal Server Error"})

    redis_client.set(unique_key,
                     json.dumps(shorten),
                     ex=CACHE_TTL)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=shorten,
        media_type="application/json"
    )


@app.get("/shorten/{shortened_url}")
async def get_url(
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

    try:
        db.increment_views(shortened_url)
    except Exception as e:
        print(e)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content="Internal server error")

    return RedirectResponse(url=data['shortened_url'],
                            status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@app.get("/shorten/{shortened_url}/stats", response_model=URLStats)
async def get_url_stats(
        request: Request,
        shortened_url: Annotated[str, Path(title="Shortened URL")]
):
    try:
        data = db.get_entry(shortened_url)
    except Exception as e:
        print(e)
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND)

    return JSONResponse(status_code=status.HTTP_200_OK, content=data)


@app.patch('/shorten/{shortened_url}')
async def update_shortened_url(
    request: Request,
    shortened_url: Annotated[str, Path(title="Shortened URL")],
    new_original_url: str,
):
    try:
        data = db.update_entry(new_original_url, shortened_url)
    except Exception as e:
        print(e)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content="Internal server error")

    unique_key = request.state.unique_key
    redis_client.set(unique_key,
                     json.dumps(data),
                     ex=CACHE_TTL)

    return JSONResponse(status_code=status.HTTP_200_OK, content=data)


@app.delete('/shorten/{shortened_url}')
async def delete_shortened_url(
    request: Request,
    shortened_url: Annotated[str, Path(title="Shortened URL")]
):
    try:
        data = db.delete_entry(shortened_url)
    except Exception as e:
        print(e)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content="Internal server error")

    unique_key = request.state.unique_key
    redis_client.delete(unique_key)

    return JSONResponse(status_code=status.HTTP_200_OK, content=data)


@app.get("/redis")
async def read_redis():
    return redis_client.scan(0)


@app.get("/db")
async def read_db():
    return db.get_all_entries()
