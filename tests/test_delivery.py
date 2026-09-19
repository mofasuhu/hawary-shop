"""Tests for delivery fee calculation."""
from flask import g

from app.extensions import db
from app.hooks import load_translation
from app.models.delivery import GovernorateDeliveryFee
from app.models.product import Product, ProductSize
from app.services.delivery import calculate_delivery_fees


def test_calculate_delivery_fees_success(app, _db, seed_translations):
    with app.app_context():
        product = Product(
            name_en="P",
            name_ar="P",
            category_en="C",
            category_ar="C",
            ingredients_en="I",
            ingredients_ar="I",
            gender_en="U",
            gender_ar="U",
            description_en="D",
            description_ar="D",
            image_url="x.jpg",
        )
        db.session.add(product)
        db.session.flush()

        size = ProductSize(
            product_id=product.id,
            size_en="S",
            size_ar="S",
            price=50.0,
            available_quantity=5,
            weight_kg=1.0,
            length_cm=1.0,
            width_cm=1.0,
            height_cm=1.0,
            delivery_factor=2.0,
        )
        db.session.add(size)
        db.session.add(
            GovernorateDeliveryFee(
                governorate_name="cairo",
                base_fee=50.0,
                per_kg_rate=5.5,
                is_covered=True,
            )
        )
        db.session.commit()

        db.session.refresh(size)
        order_data = {f"{product.id}_{size.id}": {"quantity": 2}}
        g.translations = load_translation("en")
        fees, message = calculate_delivery_fees("cairo", order_data)

        assert message == "Success"
        expected = int(50.0 + (2 * size.delivery_factor * 5.5))
        assert fees == expected


def test_calculate_delivery_fees_unknown_governorate(app, _db, seed_translations):
    with app.app_context():
        g.translations = load_translation("en")
        fees, message = calculate_delivery_fees("unknown_area", {})
        assert fees == 0
        assert message != "Success"
