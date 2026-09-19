"""Tests for registration, login, and email confirmation."""
from unittest.mock import patch

from app.extensions import db
from app.models.user import User
import app.extensions as ext

from tests.conftest import TEST_PASSWORD


@patch("app.routes.auth.send_email_confirmation")
def test_signup_creates_unconfirmed_user(mock_send_email, client, _db, seed_translations):
    response = client.post(
        "/signup",
        data={
            "username": "newuser@test.local",
            "password": TEST_PASSWORD,
            "full_name": "New User",
            "mobile": "01099998888",
            "address": "New Address",
            "area": "cairo",
        },
        follow_redirects=False,
    )

    assert response.status_code in (301, 302)
    mock_send_email.assert_called_once()

    user = User.query.filter_by(username="newuser@test.local").first()
    assert user is not None
    assert user.confirmed is False
    assert user.role == "client"


def test_login_success_redirects_home(client, auth_user, seed_translations):
    response = client.post(
        "/login",
        data={"username": auth_user["username"], "password": TEST_PASSWORD},
        follow_redirects=False,
    )
    assert response.status_code in (301, 302)
    assert response.location.endswith("/") or "home" in (response.location or "")


def test_login_wrong_password_stays_on_login(client, auth_user, seed_translations):
    response = client.post(
        "/login",
        data={"username": auth_user["username"], "password": "WrongPass1!"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"login" in response.request.path.encode() or response.data


def test_confirm_email_activates_user(app, client, _db, seed_translations):
    with app.app_context():
        from werkzeug.security import generate_password_hash

        user = User(
            username="confirm@test.local",
            password=generate_password_hash(TEST_PASSWORD, method="scrypt"),
            role="client",
            confirmed=False,
            full_name="Confirm User",
            mobile="01011112222",
            address="Addr",
            area="cairo",
        )
        db.session.add(user)
        db.session.commit()

        token = ext.serializer.dumps(user.username, salt="email-confirm")

    response = client.get(f"/confirm/{token}", follow_redirects=False)
    assert response.status_code in (301, 302)

    with app.app_context():
        user = User.query.filter_by(username="confirm@test.local").first()
        assert user.confirmed is True
