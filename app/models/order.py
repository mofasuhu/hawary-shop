from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy.dialects.postgresql import TIMESTAMP
from app.extensions import db


class TempOrderData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    merchant_order_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    data = db.Column(db.Text, nullable=False)  # Store the dictionary as JSON string
    created_at = db.Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.now(ZoneInfo("UTC")))
    is_processed = db.Column(db.Boolean, default=False)  # To prevent double processing

    def __repr__(self):
        return f"<TempOrderData {self.merchant_order_id}>"


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    merchant_order_id = db.Column(db.String(100), nullable=True)
    date = db.Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.now(ZoneInfo("UTC")))
    status = db.Column(db.String(50), server_default="Pending", default="Pending", nullable=False)
    order_total_price = db.Column(db.Float, server_default="0.0", default=0.0, nullable=False)
    payment_method = db.Column(db.String(50), server_default="Cash on Delivery", default="Cash on Delivery", nullable=False)
    payment_status = db.Column(db.String(50), server_default="Pay on Delivery", default="Pay on Delivery", nullable=False)
    order_promocode_used = db.Column(db.String(100), server_default="No Promocode", default="No Promocode", nullable=False)
    order_discount_percent = db.Column(db.Float, server_default="0.0", default=0.0, nullable=False)
    delivery_fees = db.Column(db.Float, server_default="0.0", default=0.0, nullable=False)

    address = db.Column(db.String(250), nullable=False)
    area = db.Column(db.String(250), nullable=False)
    recipient_name = db.Column(db.String(150), nullable=False)
    recipient_phone = db.Column(db.String(50), nullable=False)

    user = db.relationship("User", backref=db.backref("orders", lazy=True))
    transaction = db.relationship('Transaction', backref='order', uselist=False)


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id', ondelete='CASCADE'), nullable=False)
    product_size_id = db.Column(db.Integer, db.ForeignKey('product_size.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, server_default="0.0", default=0.0, nullable=False)  # Price at time of order
    product = db.relationship("Product", backref="order_items")
    product_size = db.relationship("ProductSize")
    order = db.relationship("Order", backref=db.backref("items", lazy=True))
