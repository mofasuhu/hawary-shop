"""Startup validation for required environment variables."""
import os
import sys

_ALWAYS_REQUIRED = [
    ("SECRET_KEY", "Flask session signing and email tokens"),
    ("DATABASE_URL", "PostgreSQL database connection"),
]

_PRODUCTION_REQUIRED = [
    ("MAIL_SERVER", "SMTP server for transactional email"),
    ("MAIL_PORT", "SMTP port"),
    ("MAIL_USERNAME", "SMTP username"),
    ("MAIL_PASSWORD", "SMTP password"),
    ("MAIL_DEFAULT_SENDER", "Default From address for outgoing mail"),
    ("PAYMOB_SECRET_KEY", "Paymob API secret for card payments"),
    ("PAYMOB_PUBLIC_KEY", "Paymob public key for checkout redirect"),
    ("PAYMOB_INTEGRATION_ID", "Paymob integration ID for card payments"),
    ("PAYMOB_HMAC_SECRET", "Paymob webhook HMAC verification"),
]

_OPTIONAL_WARNINGS = [
    ("GOOGLE_CLIENT_ID", "Google OAuth sign-in"),
    ("GOOGLE_CLIENT_SECRET", "Google OAuth sign-in"),
    ("CLOUDINARY_CLOUD_NAME", "Cloudinary image uploads (admin)"),
    ("CLOUDINARY_API_KEY", "Cloudinary image uploads (admin)"),
    ("CLOUDINARY_API_SECRET", "Cloudinary image uploads (admin)"),
    ("FIRST_SUPERADMIN_MAIL", "First-run superadmin seed"),
    ("DB_HOST", "Admin database export (pg_dump)"),
    ("DB_NAME", "Admin database export (pg_dump)"),
    ("DB_USER", "Admin database export (pg_dump)"),
    ("DB_PASSWORD", "Admin database export (pg_dump)"),
]


def _is_blank(name):
    return not os.getenv(name, "").strip()


def _is_production():
    return (
        os.getenv("FLASK_ENV") == "production"
        or os.getenv("RENDER") == "1"
    )


def _should_skip():
    if os.getenv("SKIP_ENV_VALIDATION", "").strip() == "1":
        return True
    if "pytest" in sys.modules:
        return True
    return False


def validate_environment():
    """
    Validate required environment variables before the app binds extensions.
    Exits with code 1 and a clear message if anything required is missing.
    """
    if _should_skip():
        return

    missing = []
    for name, purpose in _ALWAYS_REQUIRED:
        if _is_blank(name):
            missing.append((name, purpose))

    if _is_production():
        for name, purpose in _PRODUCTION_REQUIRED:
            if _is_blank(name):
                missing.append((name, purpose))

    warnings = []
    for name, purpose in _OPTIONAL_WARNINGS:
        if _is_blank(name):
            warnings.append((name, purpose))

    if missing:
        lines = ["Missing required environment variables:", ""]
        for name, purpose in missing:
            lines.append(f"  - {name} ({purpose})")
        lines.append("")
        lines.append(
            "Set these in .env (local) or your hosting dashboard (Render), then restart."
        )
        print("\n".join(lines), file=sys.stderr)
        sys.exit(1)

    if warnings:
        lines = [
            "Optional environment variables not set (some features may not work):",
            "",
        ]
        for name, purpose in warnings:
            lines.append(f"  - {name} ({purpose})")
        print("\n".join(lines), file=sys.stderr)
