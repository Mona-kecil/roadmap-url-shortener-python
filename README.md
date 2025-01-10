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
- [ ] Abstract SQL command (create, read, update, delete) to add/modify/delete url.
- [ ] Implement soft-deletion.
- [ ] Implement create route.
    - [ ] Make it idempotent.
    - [ ] Implement rate-limiting using Redis.
    - [ ] Implement error handling.
- [ ] Implement read route.
    - [ ] Implement analytics using Redis.
        - [ ] How many times have the url been queried?
        - [ ] How many times have the url been clicked?
    - [ ] Implement error handling.
- [ ] Implement update route.
    - [ ] Make it idempotent.
    - [ ] Implement rate-limiting using Redis.
    - [ ] Implement error handling.
- [ ] Implement delete route.
    - [ ] Perform soft-delete.
    - [ ] Implement error handling.
