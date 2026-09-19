import os
from dotenv import load_dotenv

load_dotenv()

# --- Production Detection ---
IS_PROD = os.getenv("FLASK_ENV") == "production" and os.getenv("RENDER") == "1"

# --- Egypt Governorates ---
EGYPT_GOVERNORATES = [
    'cairo', 'giza', 'new_cairo', '6th_of_october', 'sheikh_zayed', 'obour', 'shorouk', 'badr', 'hadayek_october', 'hadayek_el_ahram', 'new_administrative_capital', '10th_of_ramadan', 'helwan', 'alexandria', 'new_alamein', 'dakahlia', 'red_sea', 'beheira', 'fayoum', 'gharbia', 'ismailia', 'menofia', 'minya', 'qalyubia', 'new_valley', 'suez', 'asyut', 'qena', 'damietta', 'sohag', 'north_sinai', 'south_sinai', 'kafr_el_sheikh', 'matrouh', 'luxor', 'beni_suef', 'port_said', 'sharqia', 'aswan'
]

# --- Delivery ---
DIMENSIONAL_WEIGHT_FACTOR = 5000  # cm^3 per kg

# --- Paymob ---
HMAC_SECRET = os.getenv("PAYMOB_HMAC_SECRET", "")

PAYMOB_HMAC_STRING_KEYS = [
    "amount_cents",
    "created_at",
    "currency",
    "error_occured",
    "has_parent_transaction",
    "obj.id",  # This refers to obj['id']
    "integration_id",
    "is_3d_secure",
    "is_auth",
    "is_capture",
    "is_refunded",
    "is_standalone_payment",
    "is_voided",
    "order.id",  # This refers to obj['order']['id']
    "owner",
    "pending",
    "source_data.pan",
    "source_data.sub_type",
    "source_data.type",
    "success"
]

# --- Content Security Policy ---
CSP = {
    'default-src': ["'self'"],
    'script-src': ["'self'", "'unsafe-inline'"],
    'style-src': [
        "'self'",
        "'unsafe-inline'",
        "https://fonts.googleapis.com",
        "https://cdnjs.cloudflare.com",
    ],
    'font-src': [
        "'self'",
        "https://fonts.gstatic.com",
        "https://cdnjs.cloudflare.com",
    ],
    'img-src': ["'self'", "data:", "https://res.cloudinary.com"],
    'connect-src': [
        "'self'",
        "https://accounts.google.com",
        "https://www.googleapis.com",
    ],
    'frame-src': ["'self'", "https://accept.paymob.com"],
    'object-src': ["'none'"],
    'base-uri': ["'self'"],
    'form-action': ["'self'", "https://accounts.google.com", "https://accept.paymob.com"],
}

# --- Google OAuth Parameters ---
GOOGLE_OAUTH_CONFIG = {
    'client_id': os.getenv('GOOGLE_CLIENT_ID'),
    'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
    'access_token_url': 'https://accounts.google.com/o/oauth2/token',
    'access_token_params': None,
    'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
    'authorize_params': None,
    'api_base_url': 'https://www.googleapis.com/oauth2/v1/',
    'userinfo_endpoint': 'https://www.googleapis.com/oauth2/v1/userinfo',
    'client_kwargs': {'scope': 'profile email'},
}


class Config:
    """Flask application configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mail
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = os.getenv('MAIL_PORT')
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    MAIL_TIMEOUT = int(os.getenv('MAIL_TIMEOUT', '10'))

    # Cache
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300

    # Session / Cookie security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "None" if IS_PROD else "Lax"
    SESSION_COOKIE_SECURE = IS_PROD
    REMEMBER_COOKIE_SAMESITE = "None" if IS_PROD else "Lax"
    REMEMBER_COOKIE_SECURE = IS_PROD
    PREFERRED_URL_SCHEME = "https" if IS_PROD else "http"

    # Cloudinary
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

    # Superadmin seed
    FIRST_SUPERADMIN_MAIL = os.getenv('FIRST_SUPERADMIN_MAIL')
    FIRST_SUPERADMIN_PASSWORD = os.getenv('FIRST_SUPERADMIN_PASSWORD')
    FIRST_SUPERADMIN_FULLNAME = os.getenv('FIRST_SUPERADMIN_FULLNAME')
    FIRST_SUPERADMIN_MOBILE = os.getenv('FIRST_SUPERADMIN_MOBILE')
    FIRST_SUPERADMIN_ADDRESS = os.getenv('FIRST_SUPERADMIN_ADDRESS')
    FIRST_SUPERADMIN_AREA = os.getenv('FIRST_SUPERADMIN_AREA')
