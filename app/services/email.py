import secrets
import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from flask import current_app, g, render_template, url_for
from flask_mail import Message
from app.extensions import db, mail
from app.models.user import User


def _default_sender():
    app = current_app._get_current_object()
    return app.config.get('MAIL_DEFAULT_SENDER') or app.config.get('MAIL_USERNAME')


def send_mail_async(msg):
    """
    Send email in a background thread so request handlers are not blocked on SMTP.
    Failures are logged only; callers should not depend on delivery in the same request.
    """
    app = current_app._get_current_object()

    def _send():
        with app.app_context():
            try:
                mail.send(msg)
            except Exception as e:
                app.logger.error("Failed to send email: %s", e)

    thread = threading.Thread(target=_send, name="async-mail", daemon=True)
    thread.start()


def send_order_status_email(recipient, recipient_name, order_id, new_status):
    """Notify customer of order status change (non-blocking)."""
    msg = Message(
        subject=f"Hawary Shop: Order #{order_id} Status Update",
        sender=_default_sender(),
        recipients=[recipient],
        body=(
            f"Hello {recipient_name},\n\n"
            f"Your order #{order_id} status has been updated to: {new_status}.\n\n"
            "Thank you for shopping with us!"
        ),
    )
    send_mail_async(msg)


def generate_reset_token(user, expires_sec=300):
    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_token_expiration = datetime.now(ZoneInfo("UTC")) + timedelta(seconds=expires_sec)
    db.session.commit()
    return token


def send_password_reset_email(user, token):
    """Password reset link (non-blocking). Build message in request context, then queue send."""
    language = 'ar' if g.current_language == 'ar' else 'en'
    reset_url = url_for('reset_password', token=token, _external=True)
    subject = g.translations['Reset_Your_Password']
    html_body = render_template('reset_password_email.html', user=user, reset_url=reset_url, language=language)
    msg = Message(
        subject=subject,
        sender=_default_sender(),
        recipients=[user.username],
        html=html_body,
    )
    send_mail_async(msg)


def verify_reset_token(token):
    from app.utils.filters import to_cairo_time
    from zoneinfo import ZoneInfo as ZI
    cairo_tz = ZI("Africa/Cairo")
    user = User.query.filter_by(reset_token=token).first()
    if user and to_cairo_time(user.reset_token_expiration) > datetime.now(cairo_tz):
        return user
    return None


def send_email_confirmation(user_email, confirm_url):
    """Signup / re-send confirmation (non-blocking). Build message in request context, then queue send."""
    language = 'ar' if g.current_language == 'ar' else 'en'
    subject = g.translations['Confirm_Your_Email']
    html_body = render_template('confirm_email.html', confirm_url=confirm_url, language=language)
    msg = Message(
        subject=subject,
        sender=_default_sender(),
        recipients=[user_email],
        html=html_body,
    )
    send_mail_async(msg)
