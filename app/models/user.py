from datetime import datetime
from zoneinfo import ZoneInfo
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import TIMESTAMP
from app.extensions import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(50), nullable=False)
    confirmed = db.Column(db.Boolean, default=False)
    full_name = db.Column(db.String(150), nullable=False)
    mobile = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(250), nullable=False)
    area = db.Column(db.String(250), nullable=False)
    superadmin = db.Column(db.Boolean, default=False)
    reset_token = db.Column(db.String(100), nullable=True, index=True)
    reset_token_expiration = db.Column(TIMESTAMP(timezone=True), nullable=True)
    last_payment_method = db.Column(db.String(50), nullable=True)
    payment_methods_used = db.Column(db.String, nullable=True)
    # --- Step 3: Admin 2FA ---
    totp_secret = db.Column(db.String(32), nullable=True)
    # --- Step 4: Account Lockout ---
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(TIMESTAMP(timezone=True), nullable=True)

    def add_payment_method(self, method):
        if self.payment_methods_used:
            methods = self.payment_methods_used.split(',')
            if method not in methods:
                methods.append(method)
                self.payment_methods_used = ','.join(methods)
                return True
        else:
            self.payment_methods_used = method
            return True
        return False


class UserCart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    cart_data = db.Column(db.JSON, nullable=False)
    updated_at = db.Column(TIMESTAMP(timezone=True), default=datetime.now(ZoneInfo("UTC")), onupdate=datetime.now(ZoneInfo("UTC")))

    user = db.relationship('User', backref=db.backref('cart', uselist=False, cascade="all, delete-orphan"))

    def __repr__(self):
        return f'<UserCart for User {self.user_id}>'


class UserWishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    products = db.Column(db.JSON, nullable=False, default=list)  # List of product IDs
    updated_at = db.Column(TIMESTAMP(timezone=True), default=datetime.now(ZoneInfo("UTC")), onupdate=datetime.now(ZoneInfo("UTC")))

    user = db.relationship('User', backref=db.backref('wishlist', uselist=False, cascade="all, delete-orphan"))

    def __repr__(self):
        return f'<UserWishlist for User {self.user_id}>'
