"""Automated smoke checks for backup parity (no DB required for most tests)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    errors = []

    # 1. Route map
    import subprocess
    r = subprocess.run(
        [sys.executable, os.path.join(os.path.dirname(__file__), "check_route_parity.py")],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        errors.append(f"route parity: {r.stdout}{r.stderr}")
    else:
        print(r.stdout.strip())

    from app import create_app
    from flask import url_for

    app = create_app()

    with app.test_request_context():
        # 2. Refund URL
        refund_url = url_for("refund_order", transaction_id=1)
        if "/admin/refund_order/1" not in refund_url:
            errors.append(f"refund URL wrong: {refund_url}")

        # 3. Bare url_for compatibility
        url_for_kwargs = {
            "refund_order": {"transaction_id": 1},
        }
        for endpoint in ("home", "login", "complete_profile", "order_client_viewer", "refund_order"):
            try:
                url_for(endpoint, **url_for_kwargs.get(endpoint, {}))
            except Exception as e:
                errors.append(f"url_for('{endpoint}'): {e}")

        # 4. Login view
        if app.login_manager.login_view != "auth.login":
            errors.append(f"login_view={app.login_manager.login_view}")

    # 5. CORS
    if not app.extensions.get("cors"):
        # flask-cors may register differently
        from flask_cors import CORS
        if CORS not in [type(x).__name__ for x in app.extensions.values()]:
            pass  # CORS wraps app, check config another way
    # Verify CORS was applied by checking after_request handlers exist
    if "flask_cors" not in str(app.extensions):
        # fallback: import path used in create_app
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "__init__.py")) as f:
            if "CORS(app" not in f.read():
                errors.append("CORS not initialized in create_app")

    # 6. Paymob webhook path exists
    rules = {r.rule: r for r in app.url_map.iter_rules()}
    webhook = "/Y5ejzepXb3XTYeeL2I81Fv4yFjhorl1Kp4gAH6waxFo553Ch88K7nWDJlPAHEHm9"
    if webhook not in rules or "POST" not in rules[webhook].methods:
        errors.append("paymob webhook route missing")

    # 7. API sizes
    api_path = "/api/product/<int:product_id>/sizes"
    if api_path not in rules:
        errors.append("API sizes route missing")

    # 8. Profile gate source
    hooks_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "hooks.py")
    with open(hooks_path) as f:
        hooks_src = f.read()
    if "allowed_endpoints" not in hooks_src or "auth.complete_profile" not in hooks_src:
        errors.append("profile gate not updated for blueprints")

    # 9. Serializer initialized and usable from auth (regression: stale import)
    import app.extensions as ext
    if ext.serializer is None:
        errors.append("ext.serializer is None after create_app()")
    else:
        token = ext.serializer.dumps("test@example.com", salt="email-confirm")
        if not token:
            errors.append("serializer.dumps returned empty token")

    # 10. Google OAuth client wired for auth blueprint
    import app.routes.auth as auth_mod
    if auth_mod.google is None:
        errors.append("auth_mod.google is None after create_app()")

    # 11. Checkout markers
    checkout_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "routes", "checkout.py")
    with open(checkout_path) as f:
        checkout_src = f.read()
    for marker in ("session['new_order']", "items_to_check", 'status == "processing"', "CRITICAL"):
        if marker not in checkout_src:
            errors.append(f"checkout missing: {marker}")

    if errors:
        print("SMOKE TEST FAILED:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print("All automated smoke checks passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
