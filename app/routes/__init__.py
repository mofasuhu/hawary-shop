from app.routes.auth import auth_bp, init_google_oauth
from app.routes.shop import shop_bp
from app.routes.cart import cart_bp
from app.routes.checkout import checkout_bp
from app.routes.customer import customer_bp
from app.routes.admin import admin_bp
from app.routes.admin_orders import admin_orders_bp
from app.routes.admin_products import admin_products_bp
from app.routes.admin_reports import admin_reports_bp
from app.routes.api import api_bp


def register_blueprints(app):
    """Register all blueprints with the Flask app."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(checkout_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_orders_bp)
    app.register_blueprint(admin_products_bp)
    app.register_blueprint(admin_reports_bp)
    app.register_blueprint(api_bp)

    # Initialize Google OAuth reference for auth blueprint
    from app.extensions import oauth
    init_google_oauth(oauth)

    app.url_map.strict_slashes = False
