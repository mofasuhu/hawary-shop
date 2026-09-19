import os
import json
import hmac
import hashlib
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.exceptions import InsecureRequestWarning
import urllib3

from flask import g, flash
from app.extensions import db
from app.models.payment import Transaction
from app.models.analytics import WebhookDebugLog
from app.config import HMAC_SECRET, PAYMOB_HMAC_STRING_KEYS

urllib3.disable_warnings(category=InsecureRequestWarning)

# Shared requests session with retry logic
req_session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
req_session.mount('https://', adapter)

cairo_tz = ZoneInfo("Africa/Cairo")


def log_to_db(log_type, message, webhook_id=None):
    """Helper function to log to DB."""
    try:
        log_entry = WebhookDebugLog(
            timestamp=datetime.now(ZoneInfo("UTC")),
            log_type=log_type,
            message=str(message),
            webhook_id=webhook_id
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        print(f"ERROR: Failed to log to DB: {e} - Original message: {message}")
        db.session.rollback()


def stringify_value_for_hmac(value):
    """
    Converts a value to its string representation as expected by Paymob for HMAC.
    """
    if isinstance(value, bool):
        return str(value).lower()
    elif value is None:
        return ""
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, dict):
        return json.dumps(value, sort_keys=True, separators=(',', ':'))
    elif isinstance(value, list):
        list_items_str = []
        for item in value:
            list_items_str.append(stringify_value_for_hmac(item))
        return "".join(list_items_str)
    else:
        return str(value)


def verify_paymob_hmac(paymob_full_payload: dict, received_hmac: str) -> bool:
    hmac_debug_id = str(uuid.uuid4())
    print("HMAC_DEBUG", f"Received HMAC: {received_hmac}", hmac_debug_id)

    if not HMAC_SECRET:
        print("ERROR", "Missing PAYMOB_HMAC_SECRET in environment", hmac_debug_id)
        return False

    concatenated_string_parts = []
    transaction_obj = paymob_full_payload.get('obj', {})

    for key_name in PAYMOB_HMAC_STRING_KEYS:
        value = None
        if key_name == "obj.id":
            value = transaction_obj.get('id')
        elif key_name == "order.id":
            order_data = transaction_obj.get('order', {})
            value = order_data.get('id')
        elif key_name.startswith("source_data."):
            source_data = transaction_obj.get('source_data', {})
            source_key = key_name.split('.')[1]
            value = source_data.get(source_key)
        else:
            value = transaction_obj.get(key_name)

        stringified_value = stringify_value_for_hmac(value)
        concatenated_string_parts.append(stringified_value)

    concatenated_string = "".join(concatenated_string_parts)

    calculated_hmac = hmac.new(
        HMAC_SECRET.encode('utf-8'),
        concatenated_string.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()

    print("HMAC_DEBUG", f"Concatenated String: {concatenated_string}", hmac_debug_id)
    print("HMAC_DEBUG", f"Calculated HMAC: {calculated_hmac}", hmac_debug_id)

    return hmac.compare_digest(calculated_hmac, received_hmac)


def handle_refund_failure(refund_data, transaction):
    if 'message' in refund_data:
        if refund_data['message'].lower() == "full amount has been already refunded":
            transaction.is_refunded = True
            transaction.refunded_amount_cents = transaction.amount_cents
            order = transaction.order
            order.payment_status = "Refunded"
            order.status = "Cancelled"
            db.session.commit()
            flash(g.translations["Full_Amount_has_been_already_refunded"], "danger")
        elif "maximum refund amount" in refund_data['message'].lower():
            refund_error_message = refund_data['message'].split(". ")[0]
            flash(f"{refund_error_message}", "danger")
        else:
            flash(f"{refund_data['message']}", "danger")
    else:
        flash(g.translations["refund_request_failed"], "danger")


def process_refund(transaction_id, refund_amount_cents):
    transaction = db.session.get(Transaction, transaction_id)
    if not transaction:
        return False, g.translations["transaction_not_found"]

    if not transaction.success or transaction.is_refunded:
        return False, g.translations["invalid_transaction_or_already_refunded"]

    if refund_amount_cents <= 0 or refund_amount_cents > transaction.net_amount_cents:
        return False, g.translations["this_amount_cant_be_refunded"]

    url = "https://accept.paymob.com/api/acceptance/void_refund/refund"
    headers = {'Authorization': f"Token {os.getenv('PAYMOB_SECRET_KEY')}", 'Content-Type': 'application/json'}
    payload = json.dumps({"transaction_id": int(transaction.transaction_id), "amount_cents": refund_amount_cents})

    try:
        response = req_session.post(url, headers=headers, data=payload)
        response.raise_for_status()
        refund_data = response.json()
    except requests.exceptions.RequestException as e:
        return False, f"Error communicating with Paymob: {e}"

    if response.status_code in [200, 201] and refund_data.get("success"):
        cairo_updated_at = datetime.strptime(refund_data["updated_at"], '%Y-%m-%dT%H:%M:%S.%f')
        cairo_updated_at = cairo_updated_at.replace(tzinfo=cairo_tz)
        utc_updated_at = cairo_updated_at.astimezone(ZoneInfo("UTC"))
        transaction.updated_at = utc_updated_at

        refunded_amount_egp = int(float(refund_data.get("data", {}).get("refunded_amount", 0)) * 100)
        transaction.refunded_amount_cents = refunded_amount_egp
        transaction.is_refunded = transaction.refunded_amount_cents >= transaction.amount_cents

        order = transaction.order
        order.payment_status = "Refunded" if transaction.is_refunded else order.payment_status
        db.session.commit()
        return True, g.translations["refund_processed_successfully"]
    else:
        error_message = g.translations["refund_request_failed"]

        if refund_data and 'message' in refund_data:
            error_message = refund_data['message']

            if "full amount has been already refunded" in refund_data['message'].lower():
                transaction.is_refunded = True
                transaction.refunded_amount_cents = transaction.amount_cents
                order = transaction.order
                order.payment_status = "Refunded"
                order.status = "Cancelled"
                db.session.commit()
            elif "maximum refund amount" in refund_data['message'].lower():
                error_message = refund_data['message'].split(". ")[0]

        elif refund_data and 'detail' in refund_data:
            error_message = refund_data['detail']

        return False, error_message
