"""Tests for cart operations and promo code preview."""
import pytest

from app.extensions import db
from app.models.payment import PromoCode
from tests.conftest import persist_user_cart


def test_update_cart_quantity_adds_item(auth_client, catalog):
    response = auth_client.post(
        "/update_cart_quantity",
        json={
            "product_id": catalog["product_id"],
            "product_size_id": catalog["size_id"],
            "quantity": 2,
        },
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["new_quantity"] == 2
    assert data["cart_count"] == 2


def test_update_cart_quantity_rejects_over_stock(auth_client, catalog):
    response = auth_client.post(
        "/update_cart_quantity",
        json={
            "product_id": catalog["product_id"],
            "product_size_id": catalog["size_id"],
            "quantity": 999,
        },
    )

    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert data.get("code") == "not_enough_stock"


def test_apply_promocode_uses_product_discount(auth_client, auth_user, catalog, app, _db):
    cart_key = f"{catalog['product_id']}_{catalog['size_id']}"
    order_data = {
        cart_key: {
            "quantity": 1,
            "price": catalog["price"],
            "product_id": catalog["product_id"],
            "product_size_id": catalog["size_id"],
        }
    }

    with app.app_context():
        db.session.add(PromoCode(code="SAVE10", discount_percent=10.0, is_used=False))
        db.session.commit()

    persist_user_cart(app, auth_user["id"], order_data)

    response = auth_client.post(
        "/apply_promocode",
        data={"promocode": "SAVE10"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"

    discounted_unit = catalog["price"] * (1 - catalog["discount_percent"] / 100)
    assert data["total_price"] == pytest.approx(discounted_unit)
    assert data["new_total_price"] == pytest.approx(discounted_unit * 0.9)
