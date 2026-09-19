import os
import json
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, g
from flask_login import login_required, current_user
from app.extensions import db, csrf
from app.models.product import Product, ProductSize
from app.models.order import Order, OrderItem, TempOrderData
from app.models.payment import Transaction, FailedTransaction, PromoCode
from app.models.delivery import GovernorateDeliveryFee
from app.models.user import User, UserCart
from app.services.delivery import calculate_delivery_fees
from app.services.payment import verify_paymob_hmac, req_session

cairo_tz = ZoneInfo("Africa/Cairo")
checkout_bp = Blueprint('checkout', __name__)


@checkout_bp.route("/send_order", methods=["POST"], endpoint='send_order')
@login_required
def send_order():
    order_data = session.get("order", {})

    delivery_zone = GovernorateDeliveryFee.query.filter_by(governorate_name=current_user.area).first()
    is_serviceable = delivery_zone and delivery_zone.is_covered

    if not delivery_zone:
        flash(g.translations["delivery_not_available_for_this_area_no_zone"], "danger")
        return redirect(url_for("order_client_viewer", is_serviceable=is_serviceable))
    if not delivery_zone.is_covered:
        flash(g.translations["delivery_not_covered_for_this_area_yet"], "danger")
        return redirect(url_for("order_client_viewer", is_serviceable=is_serviceable))

    if not order_data:
        flash(g.translations["no_items_in_order"], "danger")
        return redirect(url_for("order_client_viewer", is_serviceable=is_serviceable))

    # QUANTITY CHECK START ---
    items_to_check = {}
    for cart_key, item_data_from_session in order_data.items():
        try:
            product_id, product_size_id = map(int, cart_key.split('_'))
        except ValueError:
            flash(g.translations["invalid_item_id_in_the_cart_please_clear_cart_and_try_again"], "danger")
            return redirect(url_for("order_client_viewer", is_serviceable=is_serviceable))

        product_size = db.session.get(ProductSize, product_size_id)
        if not product_size:
            flash(g.translations["product_or_size_not_found_for_one_item_please_clear_cart_and_try_again"], "danger")
            return redirect(url_for("order_client_viewer", is_serviceable=is_serviceable))

        requested_quantity = item_data_from_session["quantity"]

        if requested_quantity > product_size.available_quantity:
            product_name = product_size.product.name_en if g.current_language == 'en' else product_size.product.name_ar
            size_name = product_size.size_en if g.current_language == 'en' else product_size.size_ar

            if product_size.available_quantity == 0:
                flash(g.translations["product_size_out_of_stock_right_now"].format(product_name=product_name, size_name=size_name), "danger")
            else:
                flash(g.translations["product_size_exceeds_available_at_order_time"].format(product_name=product_name, size_name=size_name, available_quantity=product_size.available_quantity), "danger")

            return redirect(url_for("order_client_viewer", is_serviceable=is_serviceable))

        items_to_check[product_size.id] = requested_quantity
    # QUANTITY CHECK END ---

    payment_method = request.form.get("payment_method")
    if not payment_method:
        flash(g.translations["please_select_a_payment_method"], "danger")
        return redirect(url_for("order_client_viewer", is_serviceable=is_serviceable))

    promocode_input = request.form.get("promocode")
    discount_percent = 0
    code = "No Promocode"
    promocode = None

    if promocode_input:
        code = promocode_input
        promocode = PromoCode.query.filter_by(code=code, is_used=False).first()
        if promocode:
            discount_percent = promocode.discount_percent
        else:
            flash(g.translations["invalid_or_expired_promo_code"], "danger")
            return redirect(url_for("order_client_viewer", is_serviceable=is_serviceable))

    current_user.last_payment_method = payment_method
    current_user.add_payment_method(payment_method)
    db.session.commit()

    total_price_items_only = 0.0
    items_pay = []
    original_cart_data_for_session = {}

    for cart_key, item_data_from_session in order_data.items():
        try:
            product_id, product_size_id = map(int, cart_key.split('_'))
        except ValueError:
            flash(g.translations["invalid_item_id_in_the_cart_please_clear_cart_and_try_again"], "danger")
            return redirect(url_for("order_client_viewer", is_serviceable=is_serviceable))

        product = db.session.get(Product, product_id)
        product_size = db.session.get(ProductSize, product_size_id)

        if not product or not product_size:
            flash(g.translations["product_or_size_not_found_for_one_item_please_clear_cart_and_try_again"], "danger")
            return redirect(url_for("order_client_viewer", is_serviceable=is_serviceable))

        product_discount = product.discount_percent or 0
        base_price = product_size.price * (1 - product_discount / 100)
        quantity = item_data_from_session["quantity"]

        discounted_price = base_price * (1 - discount_percent / 100)
        total_price_items_only += discounted_price * quantity

        full_product_name = f"{product.name_ar}" if g.current_language == 'ar' else f"{product.name_en}"
        truncated_product_name = (full_product_name[:47] + '...') if len(full_product_name) > 50 else full_product_name

        items_pay.append({
            "name": truncated_product_name,
            "amount": int(discounted_price * 100),
            "description": f"{product.name_ar} ({product_size.size_ar})" if g.current_language == 'ar' else f"{product.name_en} ({product_size.size_en})",
            "quantity": quantity
        })

        original_cart_data_for_session[cart_key] = {
            "product_id": product.id,
            "product_size_id": product_size.id,
            "quantity": quantity,
            "price": base_price
        }

    delivery_fees, delivery_message = calculate_delivery_fees(current_user.area, order_data)

    if delivery_message != "Success":
        flash(delivery_message, "danger")
        return redirect(url_for("order_client_viewer", is_serviceable=is_serviceable))

    grand_total = total_price_items_only + delivery_fees

    items_pay.append({
        "name": g.translations["Delivery_Fees"],
        "amount": delivery_fees * 100,
        "description": g.translations["Delivery_Fees"],
        "quantity": 1
    })

    session['new_order'] = {
        "user_id": current_user.id,
        "order_total_price": total_price_items_only,
        "order_total_price_with_delivery": grand_total,
        "payment_method": payment_method,
        "items_pay": items_pay,
        "promocode_id": promocode.id if promocode else None,
        "original_cart_data": original_cart_data_for_session,
        "delivery_fees": delivery_fees
    }

    merchant_order_id = str(uuid.uuid4())
    temp_data_to_store = {
        "user_id": current_user.id,
        "order_total_price": total_price_items_only,
        "order_total_price_with_delivery": grand_total,
        "payment_method": payment_method,
        "items_pay": items_pay,
        "promocode_id": promocode.id if promocode else None,
        "original_cart_data": original_cart_data_for_session,
        "delivery_fees": delivery_fees,
        "merchant_order_id": merchant_order_id
    }

    try:
        temp_order_record = TempOrderData(
            merchant_order_id=merchant_order_id,
            data=json.dumps(temp_data_to_store),
            created_at=datetime.now(ZoneInfo("UTC"))
        )
        db.session.add(temp_order_record)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(g.translations["payment_processing_error_session_lost"], "danger")
        print(f"Error saving temporary order data: {e}")
        return redirect(url_for("order_client_viewer", is_serviceable=is_serviceable))

    max_on_delivery_amount = 10000
    if payment_method == "Cash on Delivery" and total_price_items_only > max_on_delivery_amount:
        db.session.rollback()
        flash(g.translations["oops_cash_on_delivery_up_to_5000"].format(max_on_delivery_amount=max_on_delivery_amount), "danger")
        return redirect(url_for("order_client_viewer", is_serviceable=is_serviceable))

    min_order_amount = 5
    if total_price_items_only < min_order_amount:
        db.session.rollback()
        flash(g.translations["minimum_order_amount_is_100"].format(min_order_amount=min_order_amount), "danger")
        return redirect(url_for("order_client_viewer", is_serviceable=is_serviceable))

    payload_first_name = current_user.full_name.split()[0] if len(current_user.full_name.split()) > 0 else "Unknown"
    payload_last_name = current_user.full_name.split()[-1] if len(current_user.full_name.split()) > 0 else "Unknown"
    payload_address = current_user.address if current_user.address else "Unknown"
    payload_mobile = current_user.mobile if current_user.mobile else "Unknown"
    payload_mail = current_user.username if current_user.username else "Unknown"

    if payment_method == "Bank Card":
        api_url = "https://accept.paymob.com/v1/intention/"
        headers = {
          'Authorization': f"Token {os.getenv('PAYMOB_SECRET_KEY')}",
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
        payload = {
            "amount": int(grand_total * 100),
            "currency": "EGP",
            "expiration": 3600,
            "payment_methods": [int(os.getenv('PAYMOB_INTEGRATION_ID')), "card"],
            "items": items_pay,
            "billing_data": {
            "apartment": "",
            "first_name": payload_first_name,
            "last_name": payload_last_name,
            "street": payload_address,
            "building": "",
            "phone_number": payload_mobile,
            "country": "Egypt",
            "email": payload_mail,
            "floor": "",
            "state": ""
            },
            "special_reference": merchant_order_id,
            "customer": {
            "first_name": payload_first_name,
            "last_name": payload_last_name,
            "email": payload_mail,
            "extras": {}
            },
            "extras": {}
        }

        response = req_session.post(api_url, headers=headers, data=json.dumps(payload))

        if response.status_code in [200, 201]:
            client_secret_value = response.json().get("client_secret")
            public_key = os.getenv('PAYMOB_PUBLIC_KEY')
            # return redirect(f"https://accept.paymob.com/unifiedcheckout/?publicKey={public_key}&clientSecret={client_secret_value}")

            checkout_url = (
                "https://accept.paymob.com/unifiedcheckout/"
                f"?publicKey={public_key}&clientSecret={client_secret_value}"
            )
            return (
                "<!DOCTYPE html><html><head><meta charset='utf-8'>"
                f"<meta http-equiv='refresh' content='0;url={checkout_url}'>"
                f"<script>window.location.replace({checkout_url!r});</script>"
                "</head><body>Redirecting to payment… "
                f"<a href='{checkout_url}'>Continue</a></body></html>"
            ), 200            
        else:
            db.session.rollback()
            temp_order_record_to_delete = TempOrderData.query.filter_by(merchant_order_id=merchant_order_id).order_by(TempOrderData.id.desc()).first()
            if temp_order_record_to_delete:
                db.session.delete(temp_order_record_to_delete)
                db.session.commit()

            try:
                error_response = response.json()
                error_message = []
                for key, value in error_response.items():
                    if isinstance(value, list):
                        error_message.append(f"{key}: {', '.join(value)}")
                    elif isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            if isinstance(sub_value, list):
                                error_message.append(f"{sub_key}: {', '.join(sub_value)}")
                    elif isinstance(value, str):
                        error_message.append(f"{key}: {value}")
                error_message_str = " | ".join(error_message)
            except ValueError:
                error_message_str = g.translations["Unknown_error_occurred_Please_try_again"]
            flash(error_message_str, "danger")
            return redirect(url_for("order_client_viewer", is_serviceable=is_serviceable))

    new_order_record = Order(
        user_id=current_user.id,
        date=datetime.now(ZoneInfo("UTC")),
        order_total_price=grand_total,
        payment_method=payment_method,
        order_discount_percent=discount_percent,
        order_promocode_used=code,
        payment_status="Pay on Delivery",
        delivery_fees=delivery_fees,
        address=current_user.address,
        area=current_user.area,
        recipient_name=current_user.full_name,
        recipient_phone=current_user.mobile
    )

    db.session.add(new_order_record)
    db.session.flush()

    for cart_key, item_data_from_session in order_data.items():
        try:
            product_id, product_size_id = map(int, cart_key.split('_'))
        except ValueError:
            flash(g.translations["invalid_item_id_in_the_cart_please_clear_cart_and_try_again"], "danger")
            db.session.rollback()
            return redirect(url_for("order_client_viewer", is_serviceable=is_serviceable))

        product = db.session.get(Product, product_id)
        product_size = db.session.get(ProductSize, product_size_id)

        if not product or not product_size:
            flash(g.translations["product_or_size_not_found_for_one_item_please_clear_cart_and_try_again"], "danger")
            db.session.rollback()
            return redirect(url_for("order_client_viewer", is_serviceable=is_serviceable))

        product_discount = product.discount_percent or 0
        base_price = product_size.price * (1 - product_discount / 100)
        quantity = item_data_from_session["quantity"]
        discounted_price = base_price * (1 - discount_percent / 100)

        new_order_item = OrderItem(
            order_id=new_order_record.id,
            product_id=product.id,
            product_size_id=product_size.id,
            quantity=quantity,
            price=discounted_price
        )
        db.session.add(new_order_item)

        product_size.available_quantity -= quantity

    if promocode:
        promocode.is_used = True

    saved_cart = UserCart.query.filter_by(user_id=current_user.id).first()
    if saved_cart:
        db.session.delete(saved_cart)

    temp_order_record_to_add_is_processed_true = TempOrderData.query.filter_by(merchant_order_id=merchant_order_id).order_by(TempOrderData.id.desc()).first()
    if temp_order_record_to_add_is_processed_true:
        temp_order_record_to_add_is_processed_true.is_processed = True

    db.session.commit()
    session.pop("order", None)
    flash(g.translations["Order_sent_successfully_with_total"].format(total_price=grand_total), "success")
    return redirect(url_for("order_client_viewer", order_id=new_order_record.id, status="success", is_serviceable=is_serviceable))


@checkout_bp.route("/Y5ejzepXb3XTYeeL2I81Fv4yFjhorl1Kp4gAH6waxFo553Ch88K7nWDJlPAHEHm9", methods=["POST"], endpoint='paymob_webhook')
@csrf.exempt
def paymob_webhook():
    webhook_call_id = str(uuid.uuid4())
    try:
        paymob_data = request.json
        if not paymob_data:
            return "Invalid Data (Empty JSON)", 400
    except Exception:
        try:
            paymob_data = request.form.to_dict()
            if not paymob_data:
                return "Invalid Data (Empty Form)", 400
        except Exception:
            return "Invalid Data (Neither JSON nor Form)", 400

    received_hmac = request.args.get('hmac')
    if not received_hmac:
        return "HMAC Missing", 400

    if not verify_paymob_hmac(paymob_data, received_hmac):
        print("ERROR", "Paymob HMAC verification failed for webhook.", webhook_call_id)
        return "HMAC Verification Failed", 403

    transaction_obj = paymob_data.get('obj', {})
    txn_id = transaction_obj.get("id")
    if txn_id:
        existing_transaction = Transaction.query.filter_by(transaction_id=str(txn_id)).first()
        if existing_transaction:
            print("INFO", f"Webhook received for existing transaction {txn_id}. Acknowledged and ignored.", webhook_call_id)
            return "Webhook for existing transaction acknowledged.", 200

    success_status = transaction_obj.get("success")
    is_voided = transaction_obj.get("is_voided")
    error_occured = transaction_obj.get("error_occured")
    amount_cents = transaction_obj.get("amount_cents")
    merchant_order_id = transaction_obj.get("order", {}).get("merchant_order_id")

    if not merchant_order_id:
        print("ERROR", f"Webhook received without a merchant_order_id. Payload: {json.dumps(paymob_data)}", webhook_call_id)
        return "Merchant Order ID missing", 400

    temp_order_record = TempOrderData.query.filter_by(merchant_order_id=merchant_order_id).order_by(TempOrderData.id.desc()).first()

    if not temp_order_record:
        print("WARNING", f"Webhook received for unknown or mismatched merchant_order_id: {merchant_order_id}", webhook_call_id)
        return "Data Unknown or Mismatched", 200

    new_order_session_data = json.loads(temp_order_record.data)

    if not success_status or is_voided or error_occured:
        try:
            failed_txn = FailedTransaction(
                transaction_id=txn_id,
                user_id=new_order_session_data.get("user_id"),
                amount_cents=int(amount_cents) if amount_cents is not None else None,
                raw_payload=json.dumps(paymob_data),
                created_at=datetime.now(ZoneInfo("UTC"))
            )
            db.session.add(failed_txn)
            temp_order_record.is_processed = True
            db.session.commit()
            print("INFO", f"Failed transaction recorded for {merchant_order_id}", webhook_call_id)
            return "Failed Transaction Processed", 200
        except Exception as e:
            db.session.rollback()
            print("ERROR", f"Failed to record failed transaction for {merchant_order_id}: {e}", webhook_call_id)
            return "Internal Server Error", 500

    if success_status and not is_voided:
        try:
            expected_cents = int(new_order_session_data["order_total_price_with_delivery"] * 100)
            if int(amount_cents) != expected_cents:
                print("CRITICAL", f"Amount paid ({amount_cents}) does not match expected amount ({expected_cents})!", webhook_call_id)

                failed_txn = FailedTransaction(
                    transaction_id=txn_id,
                    user_id=new_order_session_data.get("user_id"),
                    amount_cents=int(amount_cents) if amount_cents is not None else None,
                    raw_payload=json.dumps(paymob_data),
                    created_at=datetime.now(ZoneInfo("UTC"))
                )
                db.session.add(failed_txn)
                temp_order_record.is_processed = True
                db.session.commit()

                return "Amount Mismatch", 400

            original_cart_data = new_order_session_data.get("original_cart_data", {})
            promocode_id = new_order_session_data.get("promocode_id")
            order_discount_percent = 0.0
            order_promocode_used = "No Promocode"

            if promocode_id:
                promocode = PromoCode.query.filter_by(id=promocode_id, is_used=False).first()
                if promocode:
                    promocode.is_used = True
                    order_discount_percent = promocode.discount_percent
                    order_promocode_used = promocode.code

            user_id_for_order = new_order_session_data.get("user_id")
            order_user = db.session.get(User, user_id_for_order)

            new_order_record = Order(
                user_id=user_id_for_order,
                merchant_order_id=merchant_order_id,
                date=datetime.now(ZoneInfo("UTC")),
                order_total_price=new_order_session_data["order_total_price_with_delivery"],
                payment_method=new_order_session_data["payment_method"],
                order_discount_percent=order_discount_percent,
                order_promocode_used=order_promocode_used,
                payment_status="Paid",
                delivery_fees=new_order_session_data["delivery_fees"],
                address=order_user.address,
                area=order_user.area,
                recipient_name=order_user.full_name,
                recipient_phone=order_user.mobile
            )

            db.session.add(new_order_record)
            db.session.flush()

            for cart_key, item_details in original_cart_data.items():
                product_id = item_details["product_id"]
                product_size_id = item_details["product_size_id"]
                quantity = item_details["quantity"]
                base_price = item_details["price"]
                discounted_item_price = base_price * (1 - order_discount_percent / 100)

                new_order_item = OrderItem(
                    order_id=new_order_record.id,
                    product_id=product_id,
                    product_size_id=product_size_id,
                    quantity=quantity,
                    price=discounted_item_price
                )
                db.session.add(new_order_item)

                product_size = db.session.get(ProductSize, product_size_id)
                if product_size:
                    product_size.available_quantity -= quantity

            utc_created_at = datetime.now(ZoneInfo("UTC"))
            utc_updated_at = None

            created_at_str = transaction_obj.get('created_at')
            if created_at_str:
                try:
                    naive_dt = datetime.fromisoformat(created_at_str)
                    cairo_dt = naive_dt.replace(tzinfo=cairo_tz)
                    utc_created_at = cairo_dt.astimezone(ZoneInfo("UTC"))
                except ValueError:
                    print("WARNING", f"Could not parse created_at_str: {created_at_str}", webhook_call_id)
                    utc_created_at = datetime.now(ZoneInfo("UTC"))

            updated_at_str = transaction_obj.get('updated_at')
            if updated_at_str:
                try:
                    naive_dt = datetime.fromisoformat(updated_at_str)
                    cairo_dt = naive_dt.replace(tzinfo=cairo_tz)
                    utc_updated_at = cairo_dt.astimezone(ZoneInfo("UTC"))
                except ValueError:
                    print("WARNING", f"Could not parse updated_at_str: {updated_at_str}", webhook_call_id)
                    pass

            transaction = Transaction(
                order_id=new_order_record.id,
                transaction_id=txn_id,
                amount_cents=int(transaction_obj.get('amount_cents', 0)),
                currency=transaction_obj.get('currency', 'unknown'),
                txn_response_code=transaction_obj.get('data', {}).get('txn_response_code', 'unknown'),
                success=success_status,
                is_3d_secure=transaction_obj.get('is_3d_secure'),
                payment_type=transaction_obj.get('source_data', {}).get('type', 'unknown'),
                payment_sub_type=transaction_obj.get('source_data', {}).get('sub_type', 'unknown'),
                created_at=utc_created_at,
                updated_at=utc_updated_at,
                is_voided=is_voided,
                is_refunded=transaction_obj.get('is_refunded'),
                is_settled=transaction_obj.get('is_settled'),
                refunded_amount_cents=int(transaction_obj.get('refunded_amount_cents', 0)),
                captured_amount_cents=int(transaction_obj.get('captured_amount_cents', 0)),
                error_occured=error_occured
            )

            db.session.add(transaction)
            temp_order_record.is_processed = True

            saved_cart = UserCart.query.filter_by(user_id=user_id_for_order).first()
            if saved_cart:
                db.session.delete(saved_cart)

            db.session.commit()
            session.pop("order", None)
            session.pop("new_order", None)
            print("INFO", f"Successful transaction processed for {merchant_order_id}", webhook_call_id)
            return "Success", 200
        except Exception as e:
            db.session.rollback()
            print("ERROR", f"Webhook processing failed for {merchant_order_id}: {e}", webhook_call_id)
            if temp_order_record and not temp_order_record.is_processed:
                temp_order_record.is_processed = True
                db.session.commit()
            return "Internal Server Error", 500

    print("INFO", f"Unexpected status for {merchant_order_id}. Data: {paymob_data}", webhook_call_id)
    return "Unexpected Status", 200


@checkout_bp.route("/paymob_redirect_handler", methods=["GET"], endpoint='paymob_redirect_handler')
def paymob_redirect_handler():
    merchant_order_id = request.args.get('merchant_order_id')
    paymob_success_status = request.args.get('success') == 'true'
    if paymob_success_status:
        flash(g.translations["payment_successful_processing_order"], "success")
        status_to_pass = "processing"  # Indicate that the order is being processed by webhook

        saved_cart = UserCart.query.filter_by(user_id=current_user.id).first()
        if saved_cart:
            db.session.delete(saved_cart)
            db.session.commit()

        session.pop("order", None)
        session.pop("new_order", None)
    else:
        flash(g.translations["payment_failed_please_try_again"], "danger")
        status_to_pass = "failed"

    delivery_zone = GovernorateDeliveryFee.query.filter_by(governorate_name=current_user.area).first()
    is_serviceable = delivery_zone and delivery_zone.is_covered

    return redirect(url_for("order_client_viewer", status=status_to_pass, merchant_order_id=merchant_order_id, is_serviceable=is_serviceable))


@checkout_bp.route("/order_client_viewer", methods=['GET'], endpoint='order_client_viewer')
@login_required
def order_client_viewer():
    status = request.args.get('status')
    merchant_order_id = request.args.get('merchant_order_id')

    if status == "success":
        pass
    elif status == "processing":
        pass
    elif status == "failed":
        pass
    elif status == "unknown_error":
        pass

    order = session.get("order", {})
    total_price = 0.0

    order_items_for_display = []

    for cart_key, product_data in order.items():
        try:
            product_id, product_size_id = map(int, cart_key.split('_'))
        except ValueError:
            if cart_key in session["order"]:
                del session["order"][cart_key]
                session.modified = True
            continue

        product = db.session.get(Product, product_id)

        product_size = db.session.get(ProductSize, product_size_id)
        if product and product_size:
            product_discount = product.discount_percent or 0
            price = product_size.price * (1 - product_discount / 100)
            quantity = product_data["quantity"]
            total_price += price * quantity

            order_items_for_display.append({
                'product': product,
                'product_size': product_size,
                'quantity': quantity,
                'discounted_price': price,
                'cart_key': cart_key
            })
        else:
            if cart_key in session["order"]:
                del session["order"][cart_key]
                session.modified = True
            flash(g.translations["product_removed_from_cart_due_to_unavailability"], "warning")
            continue

    delivery_fees, delivery_message = calculate_delivery_fees(current_user.area, order)

    if delivery_message != "Success":
        flash(delivery_message, "danger")
        delivery_fees = 100

    grand_total = total_price + delivery_fees

    delivery_zone = GovernorateDeliveryFee.query.filter_by(governorate_name=current_user.area).first()
    is_serviceable = delivery_zone and delivery_zone.is_covered

    return render_template("order_client_viewer.html",
                           order_items=order_items_for_display,
                           total_price=total_price,
                           delivery_fees=delivery_fees,
                           grand_total=grand_total,
                           is_serviceable=is_serviceable)
