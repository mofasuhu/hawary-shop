"""Tests for Cash on Delivery order placement."""
from app.extensions import db
from app.models.order import Order, OrderItem
from app.models.product import ProductSize
from tests.conftest import persist_user_cart


def _cart_order_data(catalog, quantity=2):
    cart_key = f"{catalog['product_id']}_{catalog['size_id']}"
    return {
        cart_key: {
            "quantity": quantity,
            "price": catalog["price"],
            "name_en": catalog["name_en"],
            "name_ar": catalog["name_ar"],
            "size_en": catalog["size_en"],
            "size_ar": catalog["size_ar"],
            "product_id": catalog["product_id"],
            "product_size_id": catalog["size_id"],
        }
    }


def test_send_order_cod_creates_order_and_decrements_stock(auth_client, auth_user, catalog, app):
    persist_user_cart(app, auth_user["id"], _cart_order_data(catalog, quantity=2))

    response = auth_client.post(
        "/send_order",
        data={"payment_method": "Cash on Delivery"},
        follow_redirects=False,
    )

    assert response.status_code == 302

    with app.app_context():
        orders = Order.query.all()
        assert len(orders) == 1
        order = orders[0]
        assert order.payment_method == "Cash on Delivery"
        assert order.payment_status == "Pay on Delivery"

        items = OrderItem.query.filter_by(order_id=order.id).all()
        assert len(items) == 1
        expected_price = catalog["price"] * (1 - catalog["discount_percent"] / 100)
        assert items[0].price == expected_price
        assert items[0].quantity == 2

        refreshed_size = db.session.get(ProductSize, catalog["size_id"])
        assert refreshed_size.available_quantity == 8


def test_send_order_empty_cart_redirects(auth_client, seed_translations):
    response = auth_client.post(
        "/send_order",
        data={"payment_method": "Cash on Delivery"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "order" in (response.location or "")


def test_send_order_below_minimum_redirects(auth_client, auth_user, catalog, app):
    with app.app_context():
        size = db.session.get(ProductSize, catalog["size_id"])
        product = size.product
        size.price = 1.0
        product.discount_percent = 0.0
        db.session.commit()

    cart_key = f"{catalog['product_id']}_{catalog['size_id']}"
    persist_user_cart(
        app,
        auth_user["id"],
        {
            cart_key: {
                "quantity": 1,
                "price": 1.0,
                "product_id": catalog["product_id"],
                "product_size_id": catalog["size_id"],
            }
        },
    )

    response = auth_client.post(
        "/send_order",
        data={"payment_method": "Cash on Delivery"},
        follow_redirects=False,
    )
    assert response.status_code == 302

    with app.app_context():
        assert Order.query.count() == 0
