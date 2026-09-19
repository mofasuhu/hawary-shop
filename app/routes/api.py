from flask import Blueprint, jsonify
from app.extensions import db
from app.models.product import Product

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/product/<int:product_id>/sizes')
def get_product_sizes(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify(success=False, message="Product not found."), 404
    sizes = [{
        "id": s.id, "size_en": s.size_en, "size_ar": s.size_ar,
        "price": s.price, "available_quantity": s.available_quantity
    } for s in product.sizes]
    return jsonify(success=True, sizes=sizes)
