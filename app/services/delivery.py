from flask import g
from app.extensions import db
from app.models.product import ProductSize
from app.models.delivery import GovernorateDeliveryFee


def calculate_delivery_fees(order_area, order_data):
    governorate_fee_settings = GovernorateDeliveryFee.query.filter_by(governorate_name=order_area).first()
    if not governorate_fee_settings:
        return 0, g.translations.get("delivery_fees_not_configured_for_governorate", f"Delivery fees not configured for {order_area}.")

    base_fee = governorate_fee_settings.base_fee
    per_kg_rate = governorate_fee_settings.per_kg_rate

    total_chargeable_weight = 0.0
    for cart_key, item_data in order_data.items():
        try:
            product_id, product_size_id = map(int, cart_key.split('_'))
        except ValueError:
            continue

        product_size = db.session.get(ProductSize, product_size_id)
        if product_size:
            total_chargeable_weight += item_data['quantity'] * product_size.delivery_factor
        else:
            return 0, g.translations.get("product_size_not_found_for_delivery_calc", "Product size not found for delivery calculation.")

    total_delivery_fees = base_fee + (total_chargeable_weight * per_kg_rate)

    if total_delivery_fees < 0:
        total_delivery_fees = 0

    return int(total_delivery_fees), "Success"
