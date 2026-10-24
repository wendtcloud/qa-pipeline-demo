import uuid


def unique_sku():
    """Valid SKU (3-20 chars, A-Z 0-9 hyphen) that won't collide between tests or runs."""
    return "T-" + uuid.uuid4().hex[:8].upper()


def sku_of_length(n):
    """Valid-charset SKU of an exact length, for boundary tests."""
    return uuid.uuid4().hex.upper()[:n]


def build_payload(**overrides):
    payload = {"name": "Test item", "sku": unique_sku(), "quantity": 5, "price": 9.99}
    payload.update(overrides)
    return payload