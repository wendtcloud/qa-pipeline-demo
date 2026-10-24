# qa-pipeline-demo

![QA pipeline](https://github.com/wendtcloud/qa-pipeline-demo/actions/workflows/qa.yml/badge.svg)

A small inventory REST API with an automated test suite and a CI pipeline. I built it to practise API testing, test design and running tests in CI.

The API is deliberately simple but has clear validation rules (length limits, ranges, unique SKUs, pagination), which gives the tests real boundaries and error cases to check.

## Structure

```
app/                  Node.js / Express API, SQLite storage, Dockerfile
tests/                pytest suite (API tests, fixtures, helpers)
.github/workflows/    GitHub Actions pipeline
docker-compose.yml    Runs the API as a container
```

## The API

| Endpoint | Success | Errors |
|---|---|---|
| `GET /health` | 200 | 503 if the database is unreachable |
| `GET /items?limit=&offset=` | 200 | 400 for invalid limit or offset |
| `GET /items/:id` | 200 | 400 invalid id, 404 not found |
| `POST /items` | 201 | 400 validation, 409 duplicate SKU |
| `PUT /items/:id` | 200 | 400, 404, 409 |
| `DELETE /items/:id` | 204 | 400, 404 |

Validation rules for an item:

- `name`: string, 1-50 characters (trimmed)
- `sku`: 3-20 characters, only `A-Z`, `0-9` and `-`, must be unique
- `quantity`: integer, 0-1000
- `price`: number, 0-100000
- `limit`: integer, 1-100 (default 10), `offset`: integer >= 0

## Running it

Requires Docker, Python 3.10+ and Git.

Start the API:

```
docker compose up --build -d
docker compose ps
```

Wait until the status is `healthy`. The API is then on `http://localhost:3000`.

Set up the tests (PowerShell shown; on Linux/macOS use `source .venv/bin/activate`):

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r tests/requirements.txt
```

Run them:

```
python -m pytest -v                  # everything
python -m pytest -m smoke            # quick checks only
python -m pytest -m regression       # full suite
python -m pytest --html=reports/report.html --self-contained-html
```

The tests use `http://localhost:3000` by default. Set the `BASE_URL` environment variable to point them somewhere else.

Stop the stack with `docker compose down` (add `-v` to delete the database).

## Tests

The suite is split with pytest markers:

- **smoke**: health check, create and fetch an item, list shape, rejection of an invalid item. Fast, and tells you if the build is alive.
- **regression**: everything else.

What the regression tests cover:

- Boundary values for every field, both just inside the limit (accepted) and just outside (rejected)
- Wrong types, null values, missing fields and malformed JSON
- Create, read, update and delete, including duplicate SKUs and SKU reuse after delete
- Pagination limits, offsets, ordering and page overlap
- Invalid ids on GET, PUT and DELETE

Design choices:

- Each test uses a unique SKU, so tests do not depend on each other or on leftover data and can run in any order.
- A fixture creates test items and deletes them afterwards.
- Parametrized tables keep each boundary case to one line and give readable names in the report.
- A session fixture waits for `/health` before any test runs, so tests do not race the startup.

## CI

The workflow in `.github/workflows/qa.yml` runs on every pull request and on pushes to `main`:

1. Build the Docker image and start the stack, waiting for the container health check to pass
2. Run the smoke tests
3. Run the regression tests
4. Print container logs if something failed
5. Upload the HTML reports as a build artifact
6. Tear the stack down

Smoke runs first so that a broken build fails in seconds instead of after the full suite. Branch protection on `main` requires the pipeline to pass before a pull request can be merged.
