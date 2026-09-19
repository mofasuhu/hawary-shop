"""Tests for non-blocking email helpers."""
import time
from unittest.mock import patch

from flask_mail import Message

from app.services import email as email_service


def test_send_mail_async_does_not_block(app):
    """Background send returns immediately; mail.send runs on another thread."""
    with app.app_context():
        msg = Message("Test", recipients=["test@example.com"], body="hi")
        with patch.object(email_service.mail, "send") as mock_send:
            email_service.send_mail_async(msg)
            time.sleep(0.2)
        mock_send.assert_called_once()


def test_send_order_status_email_queues_async(app):
    with app.app_context():
        with patch.object(email_service, "send_mail_async") as mock_async:
            email_service.send_order_status_email(
                "client@test.local",
                "Test User",
                42,
                "Shipped",
            )
        mock_async.assert_called_once()
        msg = mock_async.call_args[0][0]
        assert msg.recipients == ["client@test.local"]
        assert "42" in msg.subject
        assert "Shipped" in msg.body


def test_send_password_reset_email_queues_async(app, seed_translations):
    from flask import g
    from app.hooks import load_translation
    from app.models.user import User

    user = User(
        username="reset@test.local",
        role="client",
        confirmed=True,
        full_name="Test",
        mobile="01000000000",
        address="Addr",
        area="cairo",
    )

    with app.test_request_context():
        g.translations = load_translation("en")
        g.current_language = "en"
        with patch.object(email_service, "send_mail_async") as mock_async:
            email_service.send_password_reset_email(user, "fake-token")
        mock_async.assert_called_once()
        msg = mock_async.call_args[0][0]
        assert msg.recipients == ["reset@test.local"]
        assert msg.html is not None


def test_send_email_confirmation_queues_async(app, seed_translations):
    from flask import g
    from app.hooks import load_translation

    with app.test_request_context():
        g.translations = load_translation("en")
        g.current_language = "en"
        with patch.object(email_service, "send_mail_async") as mock_async:
            email_service.send_email_confirmation(
                "new@test.local",
                "https://example.com/confirm/token",
            )
        mock_async.assert_called_once()
        msg = mock_async.call_args[0][0]
        assert msg.recipients == ["new@test.local"]
        assert msg.html is not None
