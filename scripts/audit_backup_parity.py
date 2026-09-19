#!/usr/bin/env python3
"""
Broad parity audit: restored backup monolith vs refactored app.
- Route map (backup app.py vs create_app)
- All route handler names present
- Helper functions from backup PART 2
- Stale-import risks (None then reassigned in extensions)
- High-risk handler body similarity
"""
import difflib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP_APP = os.path.join(ROOT, "Hawary_Shop backup before Code Architecture Refactoring", "app.py")
sys.path.insert(0, ROOT)

# Helpers in backup PART 2 (not route handlers)
BACKUP_HELPERS = {
    "load_user", "contains_arabic", "on_user_logged_in", "save_cart_if_modified",
    "load_cart_from_db", "calculate_delivery_factor", "inject_cart_count",
    "load_translation", "set_language", "ratelimit_handler", "require_profile_completion",
    "set_global_vars", "log_visitor_activity", "product_translate_process", "translation_key",
    "tz_aware_to_cairo_time", "to_cairo_time", "datetimeformat", "dateformat",
    "generate_reset_token", "send_password_reset_email", "verify_reset_token",
    "send_email_confirmation", "validate_username", "validate_password", "today", "mydtfmt",
    "end_date_correction", "get_product_data", "create_translation_item",
    "add_product_translations", "get_unique_values", "search_and_filter", "get_cart_count",
    "handle_refund_failure", "process_refund", "log_to_db", "stringify_value_for_hmac",
    "verify_paymob_hmac", "calculate_delivery_fees", "save_cart_to_db", "clean_urls",
}

REFACTORED_HELPER_LOCATIONS = {
    "load_user": "app/hooks.py",
    "contains_arabic": "app/utils/filters.py",
    "on_user_logged_in": "app/hooks.py",
    "save_cart_if_modified": "app/hooks.py",
    "load_cart_from_db": "app/hooks.py",
    "calculate_delivery_factor": "app/models/product.py",
    "inject_cart_count": "app/hooks.py",
    "load_translation": "app/hooks.py",
    "set_language": "app/hooks.py",
    "ratelimit_handler": "app/hooks.py",
    "require_profile_completion": "app/hooks.py",
    "set_global_vars": "app/hooks.py",
    "log_visitor_activity": "app/hooks.py",
    "product_translate_process": "app/utils/filters.py",
    "translation_key": "app/utils/filters.py",
    "tz_aware_to_cairo_time": "app/utils/filters.py",
    "to_cairo_time": "app/utils/filters.py",
    "datetimeformat": "app/utils/filters.py",
    "dateformat": "app/utils/filters.py",
    "generate_reset_token": "app/services/email.py",
    "send_password_reset_email": "app/services/email.py",
    "verify_reset_token": "app/services/email.py",
    "send_email_confirmation": "app/services/email.py",
    "validate_username": "app/utils/validators.py",
    "validate_password": "app/utils/validators.py",
    "today": "app/utils/helpers.py",
    "mydtfmt": "app/utils/helpers.py",
    "end_date_correction": "app/utils/helpers.py",
    "get_product_data": "app/utils/helpers.py",
    "create_translation_item": "app/utils/helpers.py",
    "add_product_translations": "app/utils/helpers.py",
    "get_unique_values": "app/utils/helpers.py",
    "search_and_filter": "app/utils/helpers.py",
    "get_cart_count": "app/utils/helpers.py",
    "handle_refund_failure": "app/services/payment.py",
    "process_refund": "app/services/payment.py",
    "log_to_db": "app/services/payment.py",
    "stringify_value_for_hmac": "app/services/payment.py",
    "verify_paymob_hmac": "app/services/payment.py",
    "calculate_delivery_fees": "app/services/delivery.py",
    "save_cart_to_db": "app/utils/helpers.py",
    "clean_urls": "app/hooks.py",
}


def backup_routes():
    with open(BACKUP_APP) as f:
        text = f.read()
    routes = set()
    for m in re.finditer(r'@app\.route\([\'"]([^\'"]+)[\'"](?:,\s*methods=\[([^\]]+)\])?', text):
        path = m.group(1)
        methods = m.group(2) or "GET"
        methods = tuple(sorted(x.strip().strip("'\"") for x in methods.split(",")))
        routes.add((path, methods))
    for m in re.finditer(r'@api\.route\([\'"]([^\'"]+)[\'"]', text):
        routes.add(("/api" + m.group(1), ("GET",)))
    return routes


def current_routes():
    from app import create_app
    app = create_app()
    routes = set()
    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue
        methods = tuple(sorted(m for m in rule.methods if m not in ("HEAD", "OPTIONS")))
        routes.add((rule.rule, methods))
    return routes


def extract_func(text, name):
    for m in re.finditer(rf"^def {name}\(", text, re.M):
        start = m.start()
        rest = text[m.end() :]
        m2 = re.search(r"^def ", rest, re.M)
        end = m.end() + (m2.start() if m2 else len(rest))
        return text[start:end]
    return None


def norm_body(s):
    return "\n".join(
        line.strip()
        for line in s.splitlines()
        if line.strip() and not line.strip().startswith("#")
    )


def collect_app_py_text():
    parts = []
    for root, _, files in os.walk(os.path.join(ROOT, "app")):
        for fn in files:
            if fn.endswith(".py"):
                parts.append(open(os.path.join(root, fn)).read())
    return "\n".join(parts)


def main():
    failures = []
    warnings = []

    if not os.path.isfile(BACKUP_APP):
        print(f"ERROR: backup not found at {BACKUP_APP}")
        sys.exit(1)

    backup = open(BACKUP_APP).read()
    current = collect_app_py_text()

    # 1. Routes
    br, cr = backup_routes(), current_routes()
    only_b, only_c = br - cr, cr - br
    if only_b or only_c:
        failures.append("route mismatch")
        for r in sorted(only_b):
            print(f"  only backup: {r}")
        for r in sorted(only_c):
            print(f"  only current: {r}")
    else:
        print(f"OK routes: {len(br)} paths match backup app.py")

    # 2. Route handlers
    part3 = backup.split("# PART 3")[1].split("# PART 4")[0]
    route_names = re.findall(r"^def (\w+)\(", part3, re.M)
    missing_handlers = [n for n in route_names if not extract_func(current, n)]
    if missing_handlers:
        failures.append(f"missing handlers: {missing_handlers}")
    else:
        print(f"OK handlers: all {len(route_names)} backup route functions exist in app/")

    # 3. PART 2 helpers (top-level or nested e.g. inside register_hooks)
    missing_helpers = []
    for h in BACKUP_HELPERS:
        if h not in backup:
            continue
        if not extract_func(current, h) and f"def {h}(" not in current:
            missing_helpers.append(h)
    if missing_helpers:
        failures.append(f"missing helpers: {missing_helpers}")
    else:
        print(f"OK helpers: {len(BACKUP_HELPERS)} backup helpers found in app/")

    # 4. Stale import scan
    stale_import_files = []
    for root, _, files in os.walk(os.path.join(ROOT, "app")):
        for fn in files:
            if not fn.endswith(".py"):
                continue
            path = os.path.join(root, fn)
            text = open(path).read()
            if re.search(r"from app\.extensions import [^\n]*\bserializer\b", text):
                stale_import_files.append(path)
    if stale_import_files:
        failures.append(f"stale serializer import in: {stale_import_files}")
    else:
        print("OK imports: no 'from app.extensions import serializer'")

    import app.extensions as ext
    from app import create_app
    create_app()
    if ext.serializer is None:
        failures.append("ext.serializer None after create_app")
    else:
        print("OK runtime: ext.serializer initialized after create_app")

    # 5. Handler similarity (warn < 85%)
    low = []
    for name in route_names:
        b = extract_func(backup, name)
        c = extract_func(current, name)
        if not b or not c:
            continue
        ratio = difflib.SequenceMatcher(None, norm_body(b), norm_body(c)).ratio()
        if ratio < 0.85:
            low.append((name, ratio))
    if low:
        print(f"WARN similarity < 85% ({len(low)} handlers) — review formatting/condensed code:")
        for name, ratio in sorted(low, key=lambda x: x[1]):
            print(f"  {name}: {ratio:.0%}")
        warnings.extend(low)
    else:
        print("OK similarity: all handlers >= 85% normalized body match")

    # 6. Critical strings in checkout/auth
    for path, needles in [
        ("app/routes/checkout.py", ("session['new_order']", "items_to_check", "CRITICAL")),
        ("app/routes/auth.py", ("ext.serializer", "init_google_oauth")),
        ("app/hooks.py", ("allowed_endpoints", "auth.complete_profile")),
        ("app/__init__.py", ("CORS(app", "FIRST_SUPERADMIN_MAIL", "db.create_all")),
        ("app/routes/admin_orders.py", ("/admin/refund_order/",)),
    ]:
        text = open(os.path.join(ROOT, path)).read()
        for n in needles:
            if n not in text:
                failures.append(f"missing {n} in {path}")

    if failures:
        print("\nAUDIT FAILED:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print("\nAUDIT PASSED (see WARN lines for condensed handlers to spot-check manually).")
    sys.exit(0)


if __name__ == "__main__":
    main()
