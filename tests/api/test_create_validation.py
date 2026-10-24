import pytest

from helpers import build_payload, sku_of_length

pytestmark = pytest.mark.regression

# ---- Valid values at the edges: must be accepted (201) ----
VALID_BOUNDARIES = [
    pytest.param({"name": "A"}, id="name-length-1"),
    pytest.param({"name": "A" * 50}, id="name-length-50"),
    pytest.param({"sku": sku_of_length(3)}, id="sku-length-3"),
    pytest.param({"sku": sku_of_length(20)}, id="sku-length-20"),
    pytest.param({"sku": "A-B-C-1-2-3-X-Y"}, id="sku-with-hyphens"),
    pytest.param({"quantity": 0}, id="quantity-min-0"),
    pytest.param({"quantity": 1000}, id="quantity-max-1000"),
    pytest.param({"price": 0}, id="price-min-0"),
    pytest.param({"price": 0.01}, id="price-smallest-cent"),
    pytest.param({"price": 100000}, id="price-max-100000"),
]


@pytest.mark.parametrize("overrides", VALID_BOUNDARIES)
def test_valid_boundary_values_are_accepted(make_item, overrides):
    response = make_item(**overrides)
    assert response.status_code == 201, response.text


# ---- Invalid values just outside the edges: must be rejected (400) ----
# Each case breaks exactly one field, so we can assert exactly one error.
INVALID_VALUES = [
    pytest.param("name", "", id="name-empty"),
    pytest.param("name", "   ", id="name-whitespace-only"),
    pytest.param("name", "A" * 51, id="name-length-51"),
    pytest.param("name", 123, id="name-wrong-type-number"),
    pytest.param("name", None, id="name-null"),
    pytest.param("sku", "AB", id="sku-length-2"),
    pytest.param("sku", "A" * 21, id="sku-length-21"),
    pytest.param("sku", "abc-123", id="sku-lowercase"),
    pytest.param("sku", "ABC_123", id="sku-underscore"),
    pytest.param("sku", "ABC 123", id="sku-space"),
    pytest.param("sku", "ABC!@#", id="sku-special-chars"),
    pytest.param("sku", 12345, id="sku-wrong-type-number"),
    pytest.param("quantity", -1, id="quantity-negative"),
    pytest.param("quantity", 1001, id="quantity-1001"),
    pytest.param("quantity", 5.5, id="quantity-decimal"),
    pytest.param("quantity", "5", id="quantity-string"),
    pytest.param("quantity", True, id="quantity-boolean"),
    pytest.param("quantity", None, id="quantity-null"),
    pytest.param("price", -0.01, id="price-negative"),
    pytest.param("price", 100000.01, id="price-above-max"),
    pytest.param("price", "9.99", id="price-string"),
    pytest.param("price", None, id="price-null"),
]


@pytest.mark.parametrize("field, value", INVALID_VALUES)
def test_invalid_values_are_rejected(api, field, value):
    response = api.post("/items", json=build_payload(**{field: value}))
    assert response.status_code == 400
    errors = response.json()["errors"]
    assert len(errors) == 1
    assert field in errors[0]


@pytest.mark.parametrize("field", ["name", "sku", "quantity", "price"])
def test_missing_required_field_is_rejected(api, field):
    payload = build_payload()
    del payload[field]
    response = api.post("/items", json=payload)
    assert response.status_code == 400
    assert any(field in e for e in response.json()["errors"])


def test_all_fields_invalid_reports_every_error(api):
    response = api.post("/items", json={"name": "", "sku": "x", "quantity": -1, "price": "free"})
    assert response.status_code == 400
    assert len(response.json()["errors"]) == 4