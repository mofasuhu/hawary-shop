from app.extensions import db


class GovernorateDeliveryFee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    governorate_name = db.Column(db.String(255), unique=True, nullable=False)
    base_fee = db.Column(db.Float, nullable=False, default=50.0)
    per_kg_rate = db.Column(db.Float, nullable=False, default=5.5)
    is_covered = db.Column(db.Boolean, nullable=False, default=False)
