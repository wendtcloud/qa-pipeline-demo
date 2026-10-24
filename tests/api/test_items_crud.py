import json

import pytest

from helpers import build_payload

pytestmark = pytest.mark.regression

ITEM_KEYS = {"id", "name", "sku", "quantity", "price", "created_at"}


# ---------- Create ----------
def test_create_returns_complete_item(make_item):
    payload = build_payload(name="Widget", quantity=7, price=12.5)
    response = make_item(**payload)
    assert response.status_code == 201
    item = response.json()
    assert set(item) == ITEM_KEYS
    assert (item["name"], item["sku"], item["quantity"], item["price"]) == (
        "Widget", payload["sku"], 7, 12.5,
    )


def test_create_trims_name_whitespace(make_item):
    response = make_item(name="  Padded  ")
    assert response.status_code == 201
    assert response.json()["name"] == "Padded"


def test_create_duplicate_sku_returns_409(make_item):
    first = make_item()
    second = make_item(sku=first.json()["sku"])
    assert second.status_code == 409
    assert second.json()["errors"] == ["sku already exists"]


def test_create_with_malformed_json_returns_400(api):
    response = api.post("/items", data="{bad", headers={"Content-Type": "application/json"})
    assert response.status_code == 400
    assert response.json()["errors"] == ["malformed JSON"]


def test_create_with_json_array_body_returns_400(api):
    response = api.post("/items", json=[])
    assert response.status_code == 400


def test_create_with_wrong_content_type_returns_400(api):
    response = api.post(
        "/items", data=json.dumps(build_payload()), headers={"Content-Type": "text/plain"}
    )
    assert response.status_code == 400


# ---------- Read ----------
def test_get_existing_item(api, make_item):
    created = make_item().json()
    response = api.get(f"/items/{created['id']}")
    assert response.status_code == 200
    assert response.json() == created


def test_get_nonexistent_item_returns_404(api):
    response = api.get("/items/999999999")
    assert response.status_code == 404
    assert response.json()["errors"] == ["item not found"]


# ---------- Update ----------
def test_update_changes_all_fields(api, make_item):
    item = make_item().json()
    new = build_payload(name="Renamed", quantity=99, price=1.25)
    response = api.put(f"/items/{item['id']}", json=new)
    assert response.status_code == 200
    updated = response.json()
    assert (updated["name"], updated["sku"], updated["quantity"], updated["price"]) == (
        "Renamed", new["sku"], 99, 1.25,
    )
    assert api.get(f"/items/{item['id']}").json() == updated  # persisted


def test_update_keeping_same_sku_is_allowed(api, make_item):
    item = make_item().json()
    response = api.put(f"/items/{item['id']}", json=build_payload(sku=item["sku"], quantity=1))
    assert response.status_code == 200


def test_update_to_another_items_sku_returns_409(api, make_item):
    a = make_item().json()
    b = make_item().json()
    response = api.put(f"/items/{b['id']}", json=build_payload(sku=a["sku"]))
    assert response.status_code == 409


def test_update_nonexistent_item_returns_404(api):
    response = api.put("/items/999999999", json=build_payload())
    assert response.status_code == 404


def test_update_with_invalid_body_returns_400_and_changes_nothing(api, make_item):
    item = make_item().json()
    response = api.put(f"/items/{item['id']}", json=build_payload(quantity=-5))
    assert response.status_code == 400
    assert api.get(f"/items/{item['id']}").json() == item


# ---------- Delete ----------
def test_delete_removes_item(api, make_item):
    item = make_item().json()
    assert api.delete(f"/items/{item['id']}").status_code == 204
    assert api.get(f"/items/{item['id']}").status_code == 404


def test_delete_twice_returns_404_second_time(api, make_item):
    item = make_item().json()
    assert api.delete(f"/items/{item['id']}").status_code == 204
    assert api.delete(f"/items/{item['id']}").status_code == 404


def test_deleted_sku_can_be_reused(api, make_item):
    item = make_item().json()
    api.delete(f"/items/{item['id']}")
    assert make_item(sku=item["sku"]).status_code == 201


# ---------- Routing ----------
def test_unknown_route_returns_404_json(api):
    response = api.get("/does-not-exist")
    assert response.status_code == 404
    assert response.json()["errors"] == ["route not found"]