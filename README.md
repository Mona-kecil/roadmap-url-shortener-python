# Simple RESTful url shortener
project links: https://roadmap.sh/projects/url-shortening-service

# Overview
I wanna try to tackle this project using Redis.


# How to run
Best run using [uv](https://astral.sh)
- Spin up Redis server on default port
- Create virtual environment with python version >= 3.13.0
- Install dependencies
- Run main.py on src/main.py


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
- [ ] Implement update route.
    - [ ] Make it idempotent.
    - [ ] Implement rate-limiting using Redis.
    - [ ] Implement error handling.
- [ ] Implement delete route.
    - [ ] Perform soft-delete.
    - [ ] Implement error handling.
- [ ] Cache newly posted urls with TTL of 5 minutes.
