from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import event
from sqlalchemy.dialects.postgresql import TIMESTAMP
from app.extensions import db
from app.config import DIMENSIONAL_WEIGHT_FACTOR


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name_en = db.Column(db.String(500), nullable=False)  # English name
    name_ar = db.Column(db.String(500), nullable=False)  # Arabic name
    category_en = db.Column(db.String(500), nullable=False)  # English category
    category_ar = db.Column(db.String(500), nullable=False)  # Arabic category
    ingredients_en = db.Column(db.Text, nullable=False)  # ingredients in English
    ingredients_ar = db.Column(db.Text, nullable=False)  # ingredients in Arabic
    gender_en = db.Column(db.String(255), nullable=False)   # gender in English
    gender_ar = db.Column(db.String(255), nullable=False)   # gender in Arabic
    description_en = db.Column(db.Text, nullable=False)  # Description in English
    description_ar = db.Column(db.Text, nullable=False)  # Description in Arabic
    image_url = db.Column(db.String(255), nullable=False)  # Main Image
    image_url_2 = db.Column(db.String(255), nullable=True)
    image_url_3 = db.Column(db.String(255), nullable=True)
    image_url_4 = db.Column(db.String(255), nullable=True)
    image_url_5 = db.Column(db.String(255), nullable=True)
    image_url_6 = db.Column(db.String(255), nullable=True)
    image_url_7 = db.Column(db.String(255), nullable=True)
    image_url_8 = db.Column(db.String(255), nullable=True)
    image_url_9 = db.Column(db.String(255), nullable=True)
    image_url_10 = db.Column(db.String(255), nullable=True)
    discount_percent = db.Column(db.Float, nullable=False, default=0.0, server_default="0.0")


class ProductSize(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    size_en = db.Column(db.String(255), nullable=False)  # Size in English
    size_ar = db.Column(db.String(255), nullable=False)  # Size in Arabic
    price = db.Column(db.Float, nullable=False)  # Price for this size
    available_quantity = db.Column(db.Integer, nullable=False, default=0)  # available quantity for this size

    weight_kg = db.Column(db.Float, nullable=False, default=0.0)  # Weight in kilograms
    length_cm = db.Column(db.Float, nullable=False, default=0.0)  # Length in centimeters
    width_cm = db.Column(db.Float, nullable=False, default=0.0)   # Width in centimeters
    height_cm = db.Column(db.Float, nullable=False, default=0.0)  # Height in centimeters
    delivery_factor = db.Column(db.Float, nullable=False, default=0.0)  # Calculated delivery factor

    product = db.relationship('Product', backref=db.backref('sizes', lazy=True, cascade="all, delete-orphan"))


class ProductReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # e.g. 1-5
    review_text = db.Column(db.Text, nullable=True)
    created_at = db.Column(TIMESTAMP(timezone=True), default=datetime.now(ZoneInfo("UTC")))

    user = db.relationship('User', backref=db.backref('reviews', lazy=True, cascade="all, delete-orphan"))
    product = db.relationship('Product', backref=db.backref('reviews', lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f'<ProductReview for Product {self.product_id} by User {self.user_id}>'


# SQLAlchemy event listener for automatic delivery_factor calculation
@event.listens_for(ProductSize, 'before_insert')
@event.listens_for(ProductSize, 'before_update')
def calculate_delivery_factor(mapper, connection, target):
    dimensional_weight = 0.0
    if target.length_cm > 0 and target.width_cm > 0 and target.height_cm > 0:
        dimensional_weight = (target.length_cm * target.width_cm * target.height_cm) / DIMENSIONAL_WEIGHT_FACTOR
    min_delivery_factor = 0.1
    target.delivery_factor = max(target.weight_kg, dimensional_weight, min_delivery_factor)
