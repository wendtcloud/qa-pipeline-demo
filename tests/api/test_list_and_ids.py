import pytest

from helpers import build_payload

pytestmark = pytest.mark.regression


# ---------- Pagination ----------
def test_default_pagination_values(api):
    body = api.get("/items").json()
    assert body["limit"] == 10
    assert body["offset"] == 0
    assert len(body["data"]) <= 10


@pytest.mark.parametrize("limit", [1, 50, 100])
def test_valid_limit_is_respected(api, limit):
    response = api.get("/items", params={"limit": limit})
    assert response.status_code == 200
    body = response.json()
    assert body["limit"] == limit
    assert len(body["data"]) <= limit


@pytest.mark.parametrize("limit", ["0", "101", "-1", "abc", "1.5"])
def test_invalid_limit_is_rejected(api, limit):
    response = api.get("/items", params={"limit": limit})
    assert response.status_code == 400


@pytest.mark.parametrize("offset", ["-1", "abc", "1.5"])
def test_invalid_offset_is_rejected(api, offset):
    response = api.get("/items", params={"offset": offset})
    assert response.status_code == 400


def test_offset_beyond_total_returns_empty_page(api):
    response = api.get("/items", params={"offset": 1_000_000})
    assert response.status_code == 200
    assert response.json()["data"] == []


def test_pages_are_ordered_and_do_not_overlap(api, make_item):
    for _ in range(4):
        make_item()
    page1 = api.get("/items", params={"limit": 2, "offset": 0}).json()["data"]
    page2 = api.get("/items", params={"limit": 2, "offset": 2}).json()["data"]
    ids1, ids2 = [i["id"] for i in page1], [i["id"] for i in page2]
    assert set(ids1).isdisjoint(ids2)
    assert ids1 == sorted(ids1)
    assert max(ids1) < min(ids2)


def test_total_increases_after_create(api, make_item):
    before = api.get("/items").json()["total"]
    make_item()
    assert api.get("/items").json()["total"] == before + 1


# ---------- ID handling (GET / PUT / DELETE share the same parsing) ----------
BAD_IDS = ["0", "-1", "abc", "1.5", "01"]


@pytest.mark.parametrize("bad_id", BAD_IDS)
def test_get_with_invalid_id_returns_400(api, bad_id):
    assert api.get(f"/items/{bad_id}").status_code == 400


@pytest.mark.parametrize("bad_id", BAD_IDS)
def test_put_with_invalid_id_returns_400(api, bad_id):
    assert api.put(f"/items/{bad_id}", json=build_payload()).status_code == 400


@pytest.mark.parametrize("bad_id", BAD_IDS)
def test_delete_with_invalid_id_returns_400(api, bad_id):
    assert api.delete(f"/items/{bad_id}").status_code == 400