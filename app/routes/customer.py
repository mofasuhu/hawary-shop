from flask import Blueprint, render_template, redirect, url_for, flash, request, session, g, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models.user import User, UserWishlist
from app.models.product import Product, ProductReview
from app.models.order import Order
from app.models.delivery import GovernorateDeliveryFee
from app.config import EGYPT_GOVERNORATES
from app.utils.validators import validate_password
from app.services.delivery import calculate_delivery_fees
from app.services.payment import process_refund

customer_bp = Blueprint('customer', __name__)


@customer_bp.route("/currentuser_profile_editing", methods=["GET", "POST"], endpoint='currentuser_profile_editing')
@login_required
def currentuser_profile_editing():
    previous_page = request.args.get('referrer', url_for("home"))
    if request.method == "POST":
        current_user.full_name = request.form["full_name"]
        current_user.mobile = request.form["mobile"]
        current_user.address = request.form["address"]
        current_user.area = request.form["area"]
        last_payment_method = request.form.get("last_payment_method", None)
        if current_user.role == 'client' and last_payment_method:
            current_user.last_payment_method = last_payment_method
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        if new_password:
            valid, msg = validate_password(new_password)
            if not valid:
                flash(msg, "danger")
                return redirect(url_for("currentuser_profile_editing", referrer=previous_page, governorates=EGYPT_GOVERNORATES))
            if new_password == confirm_password:
                current_user.password = generate_password_hash(new_password, method='scrypt')
                flash(g.translations["password_changed_successfully"], "success")
            else:
                flash(g.translations["passwords_do_not_match_please_try_again"], "danger")
                return redirect(url_for("currentuser_profile_editing", referrer=previous_page, governorates=EGYPT_GOVERNORATES))
        db.session.commit()
        flash(g.translations["profile_updated_successfully"], "success")
        return redirect(previous_page)
    return render_template("currentuser_profile_editing.html", referrer=previous_page, governorates=EGYPT_GOVERNORATES)


@customer_bp.route('/wishlist', endpoint='wishlist')
@login_required
def wishlist():
    user_wishlist = UserWishlist.query.filter_by(user_id=current_user.id).first()
    products = []
    if user_wishlist and user_wishlist.products:
        products = Product.query.filter(Product.id.in_(user_wishlist.products)).all()
    return render_template('wishlist.html', products=products)


@customer_bp.route('/wishlist/add/<int:product_id>', methods=['POST'], endpoint='add_to_wishlist')
@login_required
def add_to_wishlist(product_id):
    user_wishlist = UserWishlist.query.filter_by(user_id=current_user.id).first()
    if not user_wishlist:
        user_wishlist = UserWishlist(user_id=current_user.id, products=[])
        db.session.add(user_wishlist)
    products = list(user_wishlist.products)
    if product_id not in products:
        products.append(product_id)
        user_wishlist.products = products
        db.session.commit()
    if request.is_json or request.headers.get('Accept', '').find('application/json') != -1:
        return jsonify(success=True, message=g.translations.get('added_to_wishlist', 'Added to Wishlist'))
    return redirect(request.referrer or url_for('home'))


@customer_bp.route('/wishlist/remove/<int:product_id>', methods=['POST'], endpoint='remove_from_wishlist')
@login_required
def remove_from_wishlist(product_id):
    user_wishlist = UserWishlist.query.filter_by(user_id=current_user.id).first()
    if user_wishlist:
        products = list(user_wishlist.products)
        if product_id in products:
            products.remove(product_id)
            user_wishlist.products = products
            db.session.commit()
    if request.is_json or request.headers.get('Accept', '').find('application/json') != -1:
        return jsonify(success=True, message=g.translations.get('removed_from_wishlist', 'Removed from Wishlist'))
    return redirect(request.referrer or url_for('wishlist'))


@customer_bp.route('/product/<int:product_id>/review', methods=['POST'], endpoint='add_product_review')
@login_required
def add_product_review(product_id):
    rating = int(request.form.get('rating', 0))
    review_text = request.form.get('review_text', '')
    if rating < 1 or rating > 5:
        flash(g.translations.get('invalid_rating', 'Invalid rating.'), 'error')
        return redirect(url_for('product_page', product_id=product_id))
    has_purchased = False
    delivered_orders = Order.query.filter_by(user_id=current_user.id, status='Delivered').all()
    for order in delivered_orders:
        if any(item.product_id == product_id for item in order.items):
            has_purchased = True
            break
    if not has_purchased:
        flash(g.translations.get('must_purchase_to_review', 'You must purchase this product to leave a review.'), 'error')
        return redirect(url_for('product_page', product_id=product_id))
    existing_review = ProductReview.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing_review:
        existing_review.rating = rating
        existing_review.review_text = review_text
    else:
        new_review = ProductReview(user_id=current_user.id, product_id=product_id, rating=rating, review_text=review_text)
        db.session.add(new_review)
    db.session.commit()
    flash(g.translations.get('review_added_successfully', 'Review added successfully!'), 'success')
    return redirect(url_for('product_page', product_id=product_id))


@customer_bp.route("/orderhistory_client_viewer", endpoint='orderhistory_client_viewer')
@login_required
def orderhistory_client_viewer():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.date.desc()).all()
    return render_template("orderhistory_client_viewer.html", orders=orders)


@customer_bp.route("/orders/edit/<int:order_id>", methods=["GET", "POST"], endpoint='client_edit_order')
@login_required
def client_edit_order(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        flash(g.translations["order_not_found"], "danger")
        return redirect(url_for("orderhistory_client_viewer"))
    if order.user_id != current_user.id:
        flash(g.translations["unauthorized_access"], "danger")
        return redirect(url_for("orderhistory_client_viewer"))
    if order.status not in ["Pending", "Preparing"]:
        flash(g.translations["you_can_only_edit_orders_with_status_pending_or_preparing"], "danger")
        return redirect(url_for("orderhistory_client_viewer"))

    if request.method == "POST":
        original_quantities = {item.id: item.quantity for item in order.items}
        proposed_order_items_for_delivery_calc = {}

        for item in list(order.items):
            remove = request.form.get(f"remove_{item.id}")
            if remove:
                if item.product_size:
                    item.product_size.available_quantity += original_quantities[item.id]
                db.session.delete(item)
            else:
                quantity_str = request.form.get(f"quantity_{item.id}")
                new_quantity = original_quantities[item.id]
                if quantity_str and int(quantity_str) >= 1:
                    new_quantity = int(quantity_str)
                quantity_difference = new_quantity - original_quantities[item.id]
                if item.product_size:
                    if quantity_difference > 0:
                        if quantity_difference > item.product_size.available_quantity:
                            flash(g.translations["cannot_add_more_than_available_for_item"].format(
                                product_name=item.product.name_en if g.current_language == 'en' else item.product.name_ar,
                                size_name=item.product_size.size_en if g.current_language == 'en' else item.product_size.size_ar,
                                available_quantity=item.product_size.available_quantity
                            ), "danger")
                            db.session.rollback()
                            return redirect(url_for("client_edit_order", order_id=order.id))
                        item.product_size.available_quantity -= quantity_difference
                    elif quantity_difference < 0:
                        item.product_size.available_quantity += abs(quantity_difference)
                item.quantity = new_quantity
                proposed_order_items_for_delivery_calc[f"{item.product_id}_{item.product_size_id}"] = {
                    "quantity": item.quantity, "price": item.price
                }

        if not proposed_order_items_for_delivery_calc:
            flash(g.translations["you_cant_remove_all_products"], "danger")
            db.session.rollback()
            return redirect(url_for("client_edit_order", order_id=order.id))

        delivery_fees, delivery_message = calculate_delivery_fees(order.area, proposed_order_items_for_delivery_calc)
        if delivery_message != "Success":
            flash(delivery_message, "danger")
            db.session.rollback()
            return redirect(url_for("client_edit_order", order_id=order.id))

        proposed_items_total_price = sum(
            item_data["quantity"] * item_data["price"]
            for item_data in proposed_order_items_for_delivery_calc.values()
        )
        proposed_grand_total = proposed_items_total_price + delivery_fees

        refund_message = ''
        if order.payment_method == "Bank Card" and order.transaction:
            captured_amount_egp = order.transaction.net_amount_cents / 100
            if proposed_grand_total > captured_amount_egp:
                flash(g.translations["edit_cant_be_done"], "danger")
                db.session.rollback()
                return redirect(url_for("client_edit_order", order_id=order.id))
            elif proposed_grand_total < captured_amount_egp:
                amount_to_be_refunded_cents = int((captured_amount_egp - proposed_grand_total) * 100)
                if amount_to_be_refunded_cents > 0:
                    success, refund_message = process_refund(order.transaction.id, amount_to_be_refunded_cents)
                    if not success:
                        flash(refund_message, "danger")
                        db.session.rollback()
                        return redirect(url_for("client_edit_order", order_id=order.id))

        order.delivery_fees = delivery_fees
        order.order_total_price = proposed_grand_total
        db.session.commit()

        if refund_message:
            flash(refund_message, "success")
        flash(g.translations["order_updated_successfully"] + " - " + str(order_id), "success")
        return redirect(url_for("orderhistory_client_viewer"))

    return render_template("client_edit_order.html", order=order, product_names=g.product_names)


@customer_bp.route("/orders/client_cancel_order/<int:order_id>", methods=["POST"], endpoint='client_cancel_order')
@login_required
def client_cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    old_status = order.status
    if old_status not in ["Pending", "Preparing"]:
        flash(g.translations["you_can_only_cancel_orders_with_status_pending_or_preparing"], "danger")
        return redirect(url_for("orderhistory_client_viewer"))

    for item in order.items:
        if item.product_size:
            item.product_size.available_quantity += item.quantity
            db.session.add(item.product_size)

    if order.payment_method == "Bank Card" and order.payment_status == "Paid" and order.transaction and not order.transaction.is_refunded:
        full_refund_amount_cents = order.transaction.net_amount_cents
        if full_refund_amount_cents > 0:
            success, message = process_refund(order.transaction.id, full_refund_amount_cents)
            if success:
                flash(message, "success")
            else:
                flash(message, "danger")
                db.session.rollback()
                return redirect(url_for("orderhistory_client_viewer"))
        else:
            flash(g.translations["order_already_fully_refunded"], "info")

    if order.payment_status != "Refunded":
        order.payment_status = "Refunded"

    order.status = "Cancelled"
    db.session.commit()
    flash(g.translations["order_status_updated_successfully"], "success")
    return redirect(url_for("orderhistory_client_viewer"))
