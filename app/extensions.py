import cloudinary
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_caching import Cache
from flask_wtf import CSRFProtect
from flask_talisman import Talisman
from authlib.integrations.flask_client import OAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from itsdangerous import URLSafeTimedSerializer

# All extension instances created WITHOUT binding to any app.
# They are bound later via init_extensions(app) inside create_app().

db = SQLAlchemy()
migrate = Migrate()

login_manager = LoginManager()
login_manager.login_view = "auth.login"

mail = Mail()
cache = Cache()
csrf = CSRFProtect()
oauth = OAuth()
talisman = Talisman()

limiter = Limiter(
    get_remote_address,
    default_limits=["10000 per day", "600 per hour"],
    storage_uri="memory://",
    strategy="fixed-window"
)

# Initialized after app config is loaded (needs SECRET_KEY)
serializer = None


def init_extensions(app):
    """Bind all extensions to the Flask app instance."""
    global serializer

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    cache.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Serializer for email tokens
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    # OAuth
    from app.config import GOOGLE_OAUTH_CONFIG
    oauth.init_app(app)
    oauth.register(name='google', **GOOGLE_OAUTH_CONFIG)

    # Talisman (CSP + security headers)
    from app.config import CSP, IS_PROD
    talisman.init_app(
        app,
        content_security_policy=CSP,
        force_https=IS_PROD,
        session_cookie_secure=IS_PROD,
    )

    # Cloudinary
    cloudinary.config(
        cloud_name=app.config.get('CLOUDINARY_CLOUD_NAME'),
        api_key=app.config.get('CLOUDINARY_API_KEY'),
        api_secret=app.config.get('CLOUDINARY_API_SECRET')
    )
