import os
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from flask import request, session, g, redirect, url_for, render_template, after_this_request
from flask_login import current_user, user_logged_in
from app.extensions import db, cache, login_manager
from app.models.user import User, UserCart
from app.models.product import Product
from app.models.translation import Translation, LowercaseDict
from app.models.analytics import VisitorLog
from app.utils.helpers import get_cart_count, save_cart_to_db


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Function to load translations with caching
@cache.memoize()
def load_translation(lang):
    translations = Translation.query.all()
    translation_dict = {}
    for translation in translations:
        if lang == 'en':
            translation_dict[translation.key] = translation.value_en
            translation_dict[translation.key.lower()] = translation.value_en
        elif lang == 'ar':
            translation_dict[translation.key] = translation.value_ar
            translation_dict[translation.key.lower()] = translation.value_ar
    return LowercaseDict(translation_dict)


def register_hooks(app):
    """Register all before_request, after_request, context processors, and signal handlers."""

    # --- Signal: on user logged in ---
    @user_logged_in.connect_via(app)
    def on_user_logged_in(sender, user, **extra):
        """Loads saved cart from DB into session when user logs in."""
        saved_cart = UserCart.query.filter_by(user_id=user.id).first()
        if saved_cart:
            session['order'] = saved_cart.cart_data
        else:
            session.pop('order', None)
        session.modified = True

    # --- After request: save cart ---
    @app.after_request
    def save_cart_if_modified(response):
        if current_user.is_authenticated and session.modified:
            save_cart_to_db()
        return response

    # --- Before request: load cart from DB ---
    @app.before_request
    def load_cart_from_db():
        if current_user.is_authenticated:
            saved_cart = UserCart.query.filter_by(user_id=current_user.id).first()
            if saved_cart:
                session['order'] = saved_cart.cart_data
            else:
                session.pop('order', None)

    # --- Before request: clean URLs ---
    @app.before_request
    def clean_urls():
        if os.environ.get("FLASK_ENV") == "production":
            if request.headers.get('X-Forwarded-Proto', 'http') == 'http':
                return redirect(request.url.replace('http://', 'https://', 1), code=301)
            if request.host == 'www.hawary.shop':
                return redirect(request.url.replace("www.hawary.shop", "hawary.shop"), code=301)
            if request.method == 'GET' and request.path != '/' and request.path.endswith('/'):
                return redirect(request.path[:-1], code=301)

    # --- Before request: set language ---
    @app.before_request
    def set_language():
        lang = request.args.get('lang') or request.cookies.get('lang')
        if lang not in ['en', 'ar']:
            lang = 'ar'
        g.translations = load_translation(lang)
        g.current_language = lang
        g.all_translations = {
            'en': load_translation('en'),
            'ar': load_translation('ar'),
        }
        g.product_names = [
            (product.id, product.name_en if g.current_language == 'en' else product.name_ar)
            for product in Product.query.all()
        ]

    # --- Error handler: rate limit ---
    @app.errorhandler(429)
    def ratelimit_handler(e):
        lang = request.args.get('lang') or request.cookies.get('lang')
        if lang not in ['en', 'ar']:
            lang = 'ar'
        g.translations = load_translation(lang)
        g.current_language = lang
        g.all_translations = {
            'en': load_translation('en'),
            'ar': load_translation('ar'),
        }
        return render_template("rate_limited.html"), 429

    # --- Before request: require profile completion ---
    @app.before_request
    def require_profile_completion():
        if request.path.startswith('/static/'):
            return None
        if current_user.is_authenticated:
            if (current_user.mobile == "not available" or
                current_user.address == "not available" or
                current_user.full_name == "not available"):
                allowed_endpoints = {
                    'complete_profile', 'logout',
                    'auth.complete_profile', 'auth.logout',
                }
                if request.endpoint not in allowed_endpoints:
                    return redirect(url_for('complete_profile'))

    # --- Before request: set global vars ---
    @app.before_request
    def set_global_vars():
        g.translations = g.translations
        g.current_language = g.current_language
        g.all_translations = g.all_translations
        g.product_names = g.product_names
        products = Product.query.all()
        g.hero_products = [
            {
                'image_url': p.image_url
            } for p in products
        ]

    # --- Before request: log visitor activity ---
    @app.before_request
    def log_visitor_activity():
        user_agent = request.headers.get('User-Agent', '')

        # Exclude Render health checks
        if 'render/' in user_agent.lower():
            return

        # Exclude known bots
        bot_keywords = ['bot.html', 'googlebot', 'python-requests']
        if any(bot_word in user_agent.lower() for bot_word in bot_keywords):
            return

        # Exclude JSON API requests without Referer
        if request.headers.get('Content-Type', '').startswith('application/json') and not request.headers.get('Referer'):
            return

        # Skip logging for static files
        if request.path.startswith('/static/'):
            return

        visitor_id = request.cookies.get('visitor_id')
        visitor = None

        if visitor_id:
            visitor = VisitorLog.query.filter_by(visitor_id=visitor_id).first()

        if visitor:
            visitor.last_seen = datetime.now(ZoneInfo("UTC"))
            db.session.commit()
            return

        new_visitor_id = str(uuid.uuid4())
        new_visitor = VisitorLog(visitor_id=new_visitor_id)
        db.session.add(new_visitor)
        db.session.commit()

        @after_this_request
        def set_visitor_cookie(response):
            two_years = timedelta(days=730)
            response.set_cookie(
                'visitor_id',
                new_visitor_id,
                max_age=two_years,
                httponly=True,
                samesite='Lax'
            )
            return response

    # --- Context processor: inject cart count ---
    @app.context_processor
    def inject_cart_count():
        return {'cart_count': get_cart_count()}
