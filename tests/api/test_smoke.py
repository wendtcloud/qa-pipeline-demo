import pytest

pytestmark = pytest.mark.smoke


def test_health_endpoint_reports_ok(api):
    response = api.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["db"] == "up"


def test_create_then_fetch_item(api, make_item):
    created = make_item(name="Smoke widget", quantity=3, price=1.5)
    assert created.status_code == 201

    item = created.json()
    assert created.headers["Location"] == f"/items/{item['id']}"

    fetched = api.get(f"/items/{item['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == item


def test_list_items_has_pagination_shape(api):
    response = api.get("/items")
    assert response.status_code == 200
    assert set(response.json()) == {"data", "total", "limit", "offset"}


def test_invalid_item_is_rejected(api):
    response = api.post("/items", json={"name": "", "sku": "x", "quantity": -1, "price": "free"})
    assert response.status_code == 400
    assert len(response.json()["errors"]) == 4