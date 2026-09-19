import os
import flask
from flask import Flask
from flask_cors import CORS
from werkzeug.security import generate_password_hash
from app.config import Config
from app.extensions import db, init_extensions
from app.hooks import register_hooks
from app.utils.filters import register_filters
from app.routes import register_blueprints
from app.models.user import User
from app.env_validation import validate_environment

# --- Backward Compatibility Patch for url_for ---
def handle_build_error(error, endpoint, values):
    """
    Catch werkzeug.routing.exceptions.BuildError and attempt to resolve
    non-namespaced endpoints (like 'home') to their blueprint-prefixed
    equivalents (like 'shop.home').
    """
    from flask import current_app, url_for
    if current_app:
        if not hasattr(current_app, '_endpoint_map'):
            current_app._endpoint_map = {}
            for rule in current_app.url_map.iter_rules():
                if '.' in rule.endpoint:
                    bare = rule.endpoint.split('.', 1)[1]
                    current_app._endpoint_map[bare] = rule.endpoint
        
        if endpoint in current_app._endpoint_map and '.' not in endpoint:
            # We found the mapped endpoint, try calling url_for again with the correct name
            new_endpoint = current_app._endpoint_map[endpoint]
            return url_for(new_endpoint, **values)
            
    # If we can't fix it, re-raise the original error
    raise error
# -----------------------------------------------

def create_app():
    """Application factory for Hawary Shop."""
    validate_environment()

    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    )

    # Load configuration
    app.config.from_object(Config)

    CORS(app, origins=[
        "https://hawary.shop",
        "https://www.hawary.shop",
    ])

    # Initialize extensions (db, mail, limiter, oauth, etc.)
    init_extensions(app)

    # Register Jinja2 filters
    register_filters(app)

    # Register request hooks, context processors, user loader
    register_hooks(app)

    # Register all route blueprints
    register_blueprints(app)

    # Register the fallback handler to gracefully catch and fix url_for lookups
    app.url_build_error_handlers.append(handle_build_error)

    # Initialize database and seed first superadmin (matches pre-refactor app.py startup)
    with app.app_context():
        try:
            db.create_all()
            if not User.query.filter_by(username=os.getenv('FIRST_SUPERADMIN_MAIL')).first():
                hashed_password = generate_password_hash(
                    os.getenv('FIRST_SUPERADMIN_PASSWORD'), method='scrypt'
                )
                superadmin_user = User(
                    username=os.getenv('FIRST_SUPERADMIN_MAIL'),
                    password=hashed_password,
                    role="admin",
                    confirmed=True,
                    full_name=os.getenv('FIRST_SUPERADMIN_FULLNAME'),
                    mobile=os.getenv('FIRST_SUPERADMIN_MOBILE'),
                    address=os.getenv('FIRST_SUPERADMIN_ADDRESS'),
                    area=os.getenv('FIRST_SUPERADMIN_AREA'),
                    superadmin=True,
                )
                db.session.add(superadmin_user)
                db.session.commit()
        except Exception as e:
            print(f"Skipping DB initialization during migration/startup due to: {e}")

    return app
