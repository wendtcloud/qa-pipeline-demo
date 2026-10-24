import os
import time

import pytest
import requests

from helpers import build_payload

BASE_URL = os.getenv("BASE_URL", "http://localhost:3000")


class ApiClient:
    """Thin wrapper so tests don't repeat the base URL and timeout."""

    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()

    def request(self, method, path, **kwargs):
        return self.session.request(method, f"{self.base_url}{path}", timeout=5, **kwargs)

    def get(self, path, **kw):
        return self.request("GET", path, **kw)

    def post(self, path, **kw):
        return self.request("POST", path, **kw)

    def put(self, path, **kw):
        return self.request("PUT", path, **kw)

    def delete(self, path, **kw):
        return self.request("DELETE", path, **kw)


@pytest.fixture(scope="session")
def base_url():
    """Wait up to 30s for the API to be healthy so tests never race startup."""
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            if requests.get(f"{BASE_URL}/health", timeout=2).ok:
                return BASE_URL
        except requests.RequestException:
            pass
        time.sleep(1)
    pytest.exit(f"API not reachable at {BASE_URL}", returncode=2)


@pytest.fixture(scope="session")
def api(base_url):
    return ApiClient(base_url)


@pytest.fixture
def make_item(api):
    """Factory fixture: creates items, then deletes them after the test."""
    created_ids = []

    def _make(**overrides):
        response = api.post("/items", json=build_payload(**overrides))
        if response.status_code == 201:
            created_ids.append(response.json()["id"])
        return response

    yield _make

    for item_id in created_ids:
        api.delete(f"/items/{item_id}")