"""Admin order management routes: edit, add items, delete, status update."""
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Blueprint, render_template, redirect, url_for, flash, request, g, jsonify, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models.product import Product, ProductSize
from app.models.order import Order, OrderItem
from app.models.payment import Transaction
from app.services.delivery import calculate_delivery_fees
from app.services.payment import process_refund
from app.services.email import send_order_status_email

admin_orders_bp = Blueprint('admin_orders', __name__)


@admin_orders_bp.route("/admin/orders/edit/<int:order_id>", methods=["GET", "POST"], endpoint='admin_edit_order')
@login_required
def admin_edit_order(order_id):
    if current_user.role != "admin":
        return redirect(url_for("home"))
    order = db.session.get(Order, order_id)
    if not order:
        flash(g.translations["order_not_found"], "danger")
        return redirect(url_for("orders_admin_viewer"))
    if order.status not in ["Pending", "Preparing"]:
        flash(g.translations["you_can_only_edit_orders_with_status_pending_or_preparing"], "danger")
        return redirect(url_for("orders_admin_viewer"))

    if request.method == "POST":
        original_quantities = {item.id: item.quantity for item in order.items}
        proposed = {}
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
                diff = new_quantity - original_quantities[item.id]
                if item.product_size:
                    if diff > 0:
                        if diff > item.product_size.available_quantity:
                            flash(g.translations["cannot_add_more_than_available_for_item"].format(
                                product_name=item.product.name_en if g.current_language == 'en' else item.product.name_ar,
                                size_name=item.product_size.size_en if g.current_language == 'en' else item.product_size.size_ar,
                                available_quantity=item.product_size.available_quantity), "danger")
                            db.session.rollback()
                            return redirect(url_for("admin_edit_order", order_id=order.id))
                        item.product_size.available_quantity -= diff
                    elif diff < 0:
                        item.product_size.available_quantity += abs(diff)
                item.quantity = new_quantity
                proposed[f"{item.product_id}_{item.product_size_id}"] = {"quantity": item.quantity, "price": item.price}

        if not proposed:
            flash(g.translations["you_cant_remove_all_products"], "danger")
            db.session.rollback()
            return redirect(url_for("admin_edit_order", order_id=order.id))

        delivery_fees, msg = calculate_delivery_fees(order.area, proposed)
        if msg != "Success":
            flash(msg, "danger"); db.session.rollback()
            return redirect(url_for("admin_edit_order", order_id=order.id))

        items_total = sum(d["quantity"] * d["price"] for d in proposed.values())
        grand = items_total + delivery_fees
        refund_message = ''
        if order.payment_method == "Bank Card" and order.transaction:
            captured = order.transaction.net_amount_cents / 100
            if grand > captured:
                flash(g.translations["edit_cant_be_done"], "danger"); db.session.rollback()
                return redirect(url_for("admin_edit_order", order_id=order.id))
            elif grand < captured and not current_user.superadmin:
                cents = int((captured - grand) * 100)
                if cents > 0:
                    ok, refund_message = process_refund(order.transaction.id, cents)
                    if not ok:
                        flash(refund_message, "danger"); db.session.rollback()
                        return redirect(url_for("admin_edit_order", order_id=order.id))

        order.delivery_fees = delivery_fees
        order.order_total_price = grand
        db.session.commit()
        if refund_message: flash(refund_message, "success")
        flash(g.translations["order_updated_successfully"] + " - " + str(order_id), "success")
        return redirect(url_for("orders_admin_viewer"))
    return render_template("admin_edit_order.html", order=order, product_names=g.product_names)


@admin_orders_bp.route("/admin/orders/admin_add_product_to_order/<int:order_id>", methods=["POST"], endpoint='admin_add_product_to_order')
@login_required
def admin_add_product_to_order(order_id):
    if current_user.role != "admin":
        return redirect(url_for("home"))
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify(message=g.translations["order_not_found"]), 404
    if order.status not in ["Pending", "Preparing"]:
        return jsonify(message=g.translations["you_can_only_edit_orders_with_status_pending_or_preparing"]), 400

    order_discount = order.order_discount_percent
    ids = request.form.getlist("new_product_id[]")
    size_ids = request.form.getlist("new_product_size_id[]")
    qtys = request.form.getlist("new_product_quantity[]")
    proposed = {}
    for item in order.items:
        proposed[f"{item.product_id}_{item.product_size_id}"] = {"quantity": item.quantity, "price": item.price, "order_item_obj": item}

    for pid_s, psid_s, q_s in zip(ids, size_ids, qtys):
        if not pid_s or not psid_s or not q_s:
            db.session.rollback()
            return jsonify(message=g.translations["all_product_size_and_quantity_fields_must_be_filled"]), 400
        try:
            pid, psid, qty = int(pid_s), int(psid_s), int(q_s)
        except ValueError:
            db.session.rollback()
            return jsonify(message=g.translations["invalid_product_id_size_id_or_quantity_format"]), 400
        if qty < 1:
            db.session.rollback()
            return jsonify(message=g.translations["Quantity_must_be_at_least_1"]), 400
        product = db.session.get(Product, pid)
        ps = db.session.get(ProductSize, psid)
        if not product or not ps or ps.product_id != product.id:
            db.session.rollback()
            return jsonify(message=g.translations["invalid_product_or_size_selected"]), 400
        ck = f"{pid}_{psid}"
        cur_qty = proposed.get(ck, {}).get("quantity", 0)
        if qty > ps.available_quantity:
            db.session.rollback()
            return jsonify(message=g.translations["cannot_add_more_than_available_for_item"].format(
                product_name=product.name_en if g.current_language == 'en' else product.name_ar,
                size_name=ps.size_en if g.current_language == 'en' else ps.size_ar,
                available_quantity=ps.available_quantity)), 400
        ps.available_quantity -= qty
        if ck in proposed:
            obj = proposed[ck]["order_item_obj"]
            obj.quantity = cur_qty + qty
            proposed[ck]["quantity"] = obj.quantity
        else:
            price = float(ps.price) * (1 - order_discount / 100)
            new_item = OrderItem(order_id=order.id, product_id=pid, product_size_id=psid, quantity=qty, price=price)
            db.session.add(new_item)
            proposed[ck] = {"quantity": qty, "price": price, "order_item_obj": new_item}

    delivery_fees, dmsg = calculate_delivery_fees(order.area, proposed)
    if dmsg != "Success":
        db.session.rollback()
        return jsonify(message=dmsg), 400
    items_total = sum(d["quantity"] * d["price"] for d in proposed.values())
    grand = items_total + delivery_fees
    if order.payment_method == "Bank Card" and order.transaction:
        if grand > order.transaction.net_amount_cents / 100:
            db.session.rollback()
            return jsonify(message=g.translations["edit_cant_be_done_new_total_exceeds_original_transaction_amount"]), 400
    order.delivery_fees = delivery_fees
    order.order_total_price = grand
    db.session.commit()
    flash(g.translations["products_added_successfully"], "success")
    return jsonify(message=""), 200


@admin_orders_bp.route("/admin/orders/delete/<int:order_id>", methods=["POST"], endpoint='superadmin_delete_order')
@login_required
def superadmin_delete_order(order_id):
    if current_user.role != "admin":
        return redirect(url_for("home"))
    order = Order.query.get_or_404(order_id)
    if order.status != "Cancelled":
        for item in order.items:
            if item.product_size:
                item.product_size.available_quantity += item.quantity
                db.session.add(item.product_size)
    for item in order.items:
        db.session.delete(item)
    if order.transaction:
        db.session.delete(order.transaction)
    db.session.delete(order)
    db.session.commit()
    flash(g.translations["order_deleted_successfully"], "success")
    return redirect(url_for("orders_admin_viewer"))


@admin_orders_bp.route("/admin/orders/update_status/<int:order_id>", methods=["POST"], endpoint='update_order_status')
@login_required
def update_order_status(order_id):
    if current_user.role != "admin":
        return redirect(url_for("home"))
    order = Order.query.get_or_404(order_id)
    old_status = order.status
    new_status = request.form["status"]

    if new_status == "Cancelled" and old_status != "Cancelled":
        for item in order.items:
            if item.product_size:
                item.product_size.available_quantity += item.quantity
                db.session.add(item.product_size)
        if order.payment_method == "Bank Card" and order.payment_status == "Paid" and order.transaction and not order.transaction.is_refunded:
            cents = order.transaction.net_amount_cents
            if cents > 0:
                ok, message = process_refund(order.transaction.id, cents)
                if ok: flash(message, "success")
                else: flash(message, "danger"); db.session.rollback(); return redirect(url_for("orders_admin_viewer"))
            else:
                flash(g.translations["order_already_fully_refunded"], "info")
        if order.payment_status != "Refunded":
            order.payment_status = "Refunded"

    order.status = new_status
    db.session.commit()
    if old_status != new_status:
        recipient = None
        if order.user and order.user.username and '@' in order.user.username:
            recipient = order.user.username
        if recipient:
            send_order_status_email(
                recipient=recipient,
                recipient_name=order.recipient_name,
                order_id=order.id,
                new_status=new_status,
            )
        else:
            current_app.logger.warning(
                "Order %s status updated but no email recipient (user_id=%s)",
                order.id,
                order.user_id,
            )
    flash(g.translations["order_status_updated_successfully"], "success")
    return redirect(url_for("orders_admin_viewer"))


@admin_orders_bp.route("/admin/refund_order/<int:transaction_id>", methods=["POST"], endpoint='refund_order')
@login_required
def refund_order(transaction_id):
    if current_user.role != "admin" and not current_user.superadmin:
        flash(g.translations["unauthorized_access"], "danger")
        return redirect(url_for("home"))
    
    refund_amount_raw = request.form.get('refund_amount', '').strip()

    try:
        refund_amount_cents = int(float(refund_amount_raw) * 100)
    except (ValueError, TypeError):
        flash(g.translations["invalid_input_please_provide_valid_values"], "danger")
        return redirect(url_for('orders_admin_viewer'))
    
    success, message = process_refund(transaction_id, refund_amount_cents)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    db.session.commit()
    return redirect(url_for('orders_admin_viewer'))
