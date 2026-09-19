import hmac
import hashlib
import json
import uuid

# Set the HMAC_SECRET directly (for testing)
HMAC_SECRET = "D9CE59CA3E24F3C29A639FC5DBAF3FBD"

# This is the specific order required by Paymob
PAYMOB_HMAC_STRING_KEYS = [
    "amount_cents",
    "created_at",
    "currency",
    "error_occured",
    "has_parent_transaction",
    "obj.id",
    "integration_id",
    "is_3d_secure",
    "is_auth",
    "is_capture",
    "is_refunded",
    "is_standalone_payment",
    "is_voided",
    "order.id",
    "owner",
    "pending",
    "source_data.pan",
    "source_data.sub_type",
    "source_data.type",
    "success"
]

def stringify_value_for_hmac(value):
    if isinstance(value, bool):
        return str(value).lower()
    elif value is None:
        return ""
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, dict):
        return json.dumps(value, sort_keys=True, separators=(',', ':'))
    elif isinstance(value, list):
        return "".join(stringify_value_for_hmac(item) for item in value)
    else:
        return str(value)

def log_to_db(tag, message, uid):
    print(f"[{tag}] ({uid}) {message}")

def verify_paymob_hmac(paymob_full_payload: dict, received_hmac: str) -> bool:
    hmac_debug_id = str(uuid.uuid4())
    log_to_db("HMAC_DEBUG", f"Full Payload for HMAC: {json.dumps(paymob_full_payload)}", hmac_debug_id)
    log_to_db("HMAC_DEBUG", f"Received HMAC: {received_hmac}", hmac_debug_id)

    if not HMAC_SECRET:
        log_to_db("ERROR", "Missing PAYMOB_HMAC_SECRET in environment", hmac_debug_id)
        return False

    transaction_obj = paymob_full_payload.get('obj', {})
    concatenated_string_parts = []

    for key_name in PAYMOB_HMAC_STRING_KEYS:
        value = None
        if key_name == "obj.id":
            value = transaction_obj.get("id")
        elif key_name == "order.id":
            value = transaction_obj.get("order", {}).get("id")
        elif key_name.startswith("source_data."):
            source_data = transaction_obj.get("source_data", {})
            source_key = key_name.split(".")[1]
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

    log_to_db("HMAC_DEBUG", f"Concatenated String: {concatenated_string}", hmac_debug_id)
    log_to_db("HMAC_DEBUG", f"Calculated HMAC: {calculated_hmac}", hmac_debug_id)

    return hmac.compare_digest(calculated_hmac, received_hmac)

# -------- TEST EXAMPLE BELOW --------

# Replace this with the actual received HMAC from Paymob webhook (you can copy it from a real webhook call)
received_hmac = "058ac6c5f8d66e10c44d4ea8eb3971a71e347b2e93d49f49ec7f18012ef019035683bc71009ac1289e51f1be33661e6219fea147534311c1f7ce0bb9f1291de0"

# Replace this with the actual payload (your example was huge; save it as a separate JSON if needed)
with open("sample_paymob_payload.json", "r", encoding="utf-8") as f:
    test_payload = json.load(f)

# Run the test
is_valid = verify_paymob_hmac(test_payload, received_hmac)
print("\n✅ HMAC is VALID!" if is_valid else "\n❌ HMAC is INVALID.")
