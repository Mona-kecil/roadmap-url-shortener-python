# Simple RESTful url shortener
project link: https://roadmap.sh/projects/url-shortening-service

# Overview
I wanna try to tackle this project using Redis.


# How to run
Best run using [uv](https://astral.sh)
- Spin up Redis server on default port
- Create virtual environment with python version listed in .pythonversion
- Install dependencies
- Run ASGI server on app.main:app (I'm using uvicorn)
- ```bash
  PYTHONPATH=$(pwd) uvicorn app.main:app
  ```
- Go to localhost:port/docs to play with the API


# Roadmaps
- [x] Create persistent data storage (SQLite3).
- [x] Abstract SQL command (create, read, update, delete) to add/modify/delete url.
- [x] Implement soft-deletion.
- [x] Implement create route.
    - [x] Make it idempotent.
    - [x] Implement rate-limiting using Redis.
    - [x] Implement error handling.
- [x] Implement read route.
    - [x] Implement analytics.
        - [x] How many times have the url been queried?
    - [x] Implement error handling.
- [x] Implement update route.
    - [x] Make it idempotent.
    - [x] Implement rate-limiting using Redis.
    - [x] Implement error handling.
- [x] Implement delete route.
    - [x] Perform soft-delete.
    - [x] Implement error handling.
- [x] Cache newly posted urls with TTL of 5 minutes.
