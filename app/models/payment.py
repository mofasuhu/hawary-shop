from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import TIMESTAMP, JSON
from app.extensions import db


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    transaction_id = db.Column(db.String(100), nullable=False)  # Paymob transaction ID
    amount_cents = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    txn_response_code = db.Column(db.String(50), nullable=False)
    success = db.Column(db.Boolean, nullable=False)
    is_3d_secure = db.Column(db.Boolean, nullable=False)
    payment_type = db.Column(db.String(50), nullable=False)  # source_data.type
    payment_sub_type = db.Column(db.String(50), nullable=False)  # source_data.sub_type
    created_at = db.Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.now(ZoneInfo("UTC")))
    updated_at = db.Column(TIMESTAMP(timezone=True), nullable=True)
    is_voided = db.Column(db.Boolean, nullable=False)
    is_refunded = db.Column(db.Boolean, nullable=False)
    is_settled = db.Column(db.Boolean, nullable=False)
    refunded_amount_cents = db.Column(db.Integer, nullable=False, default=0)
    captured_amount_cents = db.Column(db.Integer, nullable=False, default=0)
    error_occured = db.Column(db.Boolean, nullable=False)

    @hybrid_property
    def net_amount_cents(self):
        return self.amount_cents - (self.refunded_amount_cents or 0)


class FailedTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    amount_cents = db.Column(db.Integer, nullable=True)
    raw_payload = db.Column(JSON, nullable=True)
    created_at = db.Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.now(ZoneInfo("UTC")))
    user = db.relationship("User", backref="failed_transactions", lazy=True)


class PromoCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), nullable=False, unique=True)
    discount_percent = db.Column(db.Float, nullable=False)
    is_used = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<PromoCode {self.code} - {self.discount_percent}%>"
