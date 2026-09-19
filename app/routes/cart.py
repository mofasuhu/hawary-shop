from flask import Blueprint, jsonify, request, session, g, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models.product import Product, ProductSize
from app.models.delivery import GovernorateDeliveryFee
from app.models.user import UserCart
from app.models.payment import PromoCode
from app.services.delivery import calculate_delivery_fees
from app.utils.helpers import get_cart_count

cart_bp = Blueprint('cart', __name__)


def _discounted_unit_price(product, product_size):
    """Unit price after product.discount_percent (matches order_client_viewer / send_order)."""
    product_discount = product.discount_percent or 0
    return product_size.price * (1 - product_discount / 100)


@cart_bp.route("/update_cart_quantity", methods=["POST"], endpoint='update_cart_quantity')
def update_cart_quantity():
    if not request.json:
        return jsonify(success=False, message="Invalid request format"), 400

    product_id = request.json.get("product_id")
    product_size_id = request.json.get("product_size_id")
    try:
        quantity = int(request.json.get("quantity", 0))
    except (ValueError, TypeError):
        return jsonify(success=False, message=g.translations["invalid_quantity_format"]), 400

    if not product_id or not product_size_id:
        return jsonify(success=False, message=g.translations["missing_product_or_size"]), 400

    if quantity < 0:
        return jsonify(success=False, message=g.translations["quantity_cannot_be_negative"]), 400

    if "order" not in session:
        session["order"] = {}

    size_obj = db.session.get(ProductSize, product_size_id)
    if not size_obj or size_obj.product_id != product_id:
        return jsonify(success=False, message=g.translations["product_or_size_not_found_for_id"]), 400

    if quantity > size_obj.available_quantity:
        return jsonify(success=False, message=g.translations["cannot_add_more_than_available"], code="not_enough_stock"), 400

    cart_key = f"{product_id}_{size_obj.id}"

    if quantity > 0:
        product = size_obj.product
        session["order"][cart_key] = {
            "quantity": quantity,
            "price": size_obj.price,
            "name_en": product.name_en,
            "name_ar": product.name_ar,
            "size_en": size_obj.size_en,
            "size_ar": size_obj.size_ar,
            "product_id": product.id,
            "product_size_id": size_obj.id,
        }
    elif cart_key in session["order"]:
        del session["order"][cart_key]

    session.modified = True
    cart_count = get_cart_count()

    return jsonify(
        success=True,
        new_quantity=session.get("order", {}).get(cart_key, {}).get("quantity", 0),
        cart_count=cart_count
    )


@cart_bp.route('/get_order_summary', endpoint='get_order_summary')
@login_required
def get_order_summary():
    order = session.get("order", {})
    total_price = 0.0
    order_items = []

    keys_to_remove = []
    for cart_key, product_data in order.items():
        try:
            product_id, product_size_id = map(int, cart_key.split('_'))
        except ValueError:
            print(f"Warning: Malformed cart_key in session: {cart_key}")
            keys_to_remove.append(cart_key)
            continue

        product = db.session.get(Product, product_id)
        product_size = db.session.get(ProductSize, product_size_id)

        if product and product_size:
            item_price = _discounted_unit_price(product, product_size)
            item_quantity = product_data["quantity"]
            total_price += item_price * item_quantity

            order_items.append({
                "name_en": product.name_en,
                "name_ar": product.name_ar,
                "size_en": product_size.size_en,
                "size_ar": product_size.size_ar,
                "product_id": product.id,
                "product_size_id": product_size.id,
                "quantity": item_quantity,
                "price": item_price,
                "available_quantity": product_size.available_quantity,
                "image_url": product.image_url
            })
        else:
            print(f"Warning: Product or ProductSize not found for cart_key: {cart_key}. Removing from session.")
            keys_to_remove.append(cart_key)

    for key in keys_to_remove:
        if key in session["order"]:
            del session["order"][key]
    if keys_to_remove:
        session.modified = True

    delivery_fees, delivery_message = calculate_delivery_fees(current_user.area, order)
    if delivery_message != "Success":
        print(f"Error calculating delivery fees: {delivery_message}")
        delivery_fees = 100

    grand_total = total_price + delivery_fees

    delivery_zone = GovernorateDeliveryFee.query.filter_by(governorate_name=current_user.area).first()
    is_serviceable = delivery_zone and delivery_zone.is_covered

    return jsonify({
        "order_items": order_items,
        "total_price": total_price,
        "delivery_fees": delivery_fees,
        "grand_total": grand_total,
        "last_payment_method": current_user.last_payment_method,
        'is_serviceable': is_serviceable
    })


@cart_bp.route("/clear_order", methods=["POST"], endpoint='clear_order')
def clear_order():
    session.pop("order", None)

    saved_cart = UserCart.query.filter_by(user_id=current_user.id).first()
    if saved_cart:
        db.session.delete(saved_cart)
        db.session.commit()

    referrer_url = request.referrer

    delivery_zone = GovernorateDeliveryFee.query.filter_by(governorate_name=current_user.area).first()
    is_serviceable = delivery_zone and delivery_zone.is_covered

    if referrer_url and "home" in referrer_url:
        return redirect(url_for("home"))
    else:
        return redirect(url_for("order_client_viewer", is_serviceable=is_serviceable))


@cart_bp.route("/remove_from_cart", methods=["POST"], endpoint='remove_from_cart')
def remove_from_cart():
    cart_key = request.json.get("cart_key")
    order = session.get("order", {})

    if cart_key in order:
        del order[cart_key]
        session["order"] = order
        session.modified = True
        cart_count = get_cart_count()
        return jsonify(success=True, order=order, cart_count=cart_count)
    else:
        return jsonify(success=False, message=g.translations["item_not_found_in_cart"])


@cart_bp.route("/ordercard_plus_button", methods=["POST"], endpoint='ordercard_plus_button')
def ordercard_plus_button():
    cart_key = request.json.get("cart_key")
    order = session.get("order", {})

    if cart_key not in order:
        return jsonify(success=False, message=g.translations["item_not_found_in_cart_or_invalid_quantity"], code="item_not_found")

    product_id, product_size_id = map(int, cart_key.split('_'))
    size_obj = ProductSize.query.filter_by(id=product_size_id, product_id=product_id).first()

    if not size_obj:
        return jsonify(success=False, message=g.translations["product_or_size_not_found_for_one_item_please_clear_cart_and_try_again"], code="size_not_found")

    current_quantity = order[cart_key]["quantity"]
    if current_quantity >= size_obj.available_quantity:
        product_name = size_obj.product.name_en if g.current_language == 'en' else size_obj.product.name_ar
        size_name = size_obj.size_en if g.current_language == 'en' else size_obj.size_ar
        return jsonify(
            success=False,
            message=g.translations["cannot_add_more_than_available_for_item"].format(
                product_name=product_name, size_name=size_name, available_quantity=size_obj.available_quantity
            ),
            code="not_enough_stock"
        )

    order[cart_key]["quantity"] = current_quantity + 1
    session["order"] = order
    session.modified = True
    cart_count = get_cart_count()
    return jsonify(
        success=True,
        order=order,
        new_quantity=order[cart_key]["quantity"],
        cart_count=cart_count,
    )


@cart_bp.route("/ordercard_minus_button", methods=["POST"], endpoint='ordercard_minus_button')
def ordercard_minus_button():
    cart_key = request.json.get("cart_key")
    order = session.get("order", {})

    if cart_key not in order:
        return jsonify(success=False, message=g.translations["item_not_found_in_cart_or_invalid_quantity"])

    current_quantity = order[cart_key]["quantity"]
    if current_quantity > 1:
        order[cart_key]["quantity"] = current_quantity - 1
    else:
        del order[cart_key]

    session["order"] = order
    session.modified = True
    cart_count = get_cart_count()
    return jsonify(
        success=True,
        order=order,
        new_quantity=order.get(cart_key, {}).get("quantity", 0),
        cart_count=cart_count,
    )


@cart_bp.route("/apply_promocode", methods=["POST"], endpoint='apply_promocode')
@login_required
def apply_promocode():
    order = session.get("order", {})

    if not order:
        return jsonify({
            "status": "error",
            "message": g.translations["No_Items_In_Order"],
        }), 400

    total_price = 0.0
    for cart_key, product_data in order.items():
        try:
            product_id, product_size_id = map(int, cart_key.split('_'))
        except ValueError:
            continue

        product = db.session.get(Product, product_id)
        product_size = db.session.get(ProductSize, product_size_id)
        if not product or not product_size:
            continue

        price = _discounted_unit_price(product, product_size)
        quantity = int(product_data["quantity"])
        total_price += price * quantity

    delivery_fees, delivery_message = calculate_delivery_fees(current_user.area, order)
    if delivery_message != "Success":
        print(f"Error calculating delivery fees: {delivery_message}")
        delivery_fees = 100
    grand_total = total_price + delivery_fees

    promocode_input = request.form.get("promocode")
    promocode = PromoCode.query.filter_by(code=promocode_input, is_used=False).first()

    if promocode:
        discount_percent = promocode.discount_percent
        discount_amount = total_price * (discount_percent / 100)
        new_total_price = total_price - discount_amount
        new_grand_total = new_total_price + delivery_fees

        return jsonify({
            "status": "success",
            "total_price": total_price,
            "grand_total": grand_total,
            "delivery_fees": delivery_fees,
            "discount_percent": discount_percent,
            "new_total_price": new_total_price,
            "new_grand_total": new_grand_total,
            "message": f"Promo Code applied: {promocode_input}. You saved {discount_percent}%!"
        }), 200
    else:
        return jsonify({
            "status": "error",
            "message": g.translations["invalid_or_expired_promo_code"],
        }), 400
