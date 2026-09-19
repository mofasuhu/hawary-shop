from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, g, Response, send_from_directory, current_app
from flask_login import current_user
from sqlalchemy import func
from app.extensions import db
from app.models.product import Product
from app.models.order import Order
from app.models.analytics import VisitorLog
from app.utils.helpers import search_and_filter, get_unique_values, OFFERS_FILTER
from app.utils.seo import build_product_seo, site_seo

shop_bp = Blueprint('shop', __name__)


@shop_bp.route("/home", endpoint='redirect_home')
def redirect_home():
    return redirect(url_for("home"), code=301)


@shop_bp.route("/", methods=["GET"], endpoint='home')
def home():
    keyword = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()

    visitor_stats = None
    if current_user.is_authenticated and current_user.role == 'admin':
        five_minutes_ago = datetime.now(ZoneInfo("UTC")) - timedelta(minutes=5)
        current_visitors_count = db.session.query(func.count(VisitorLog.visitor_id.distinct())).filter(VisitorLog.last_seen > five_minutes_ago).scalar()
        today_start_utc = datetime.now(ZoneInfo("UTC")).replace(hour=0, minute=0, second=0, microsecond=0)
        daily_visitors_count = db.session.query(func.count(VisitorLog.visitor_id.distinct())).filter(VisitorLog.last_seen >= today_start_utc).scalar()
        visitor_stats = {
            "current": current_visitors_count,
            "daily": daily_visitors_count
        }

    page = request.args.get("page", 1, type=int)
    per_page = 15
    results = search_and_filter(keyword, category)
    total_products = len(results)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_products = results[start:end]
    categories = get_unique_values('category')

    lang = g.current_language
    if lang == "ar":
        home_desc = "تسوق منتجات مدرسية ومكتبية وعائلية من هاواري شوب — توصيل داخل مصر."
    else:
        home_desc = "Shop school, office, and family products at HAWARY SHOP — delivery across Egypt."
    seo = site_seo(lang, title=g.translations.get("top_name", "HAWARY SHOP"), description=home_desc)

    return render_template(
        "home.html",
        products=paginated_products,
        total_products=total_products,
        current_page=page,
        total_pages=(total_products + per_page - 1) // per_page,
        categories=categories,
        current_keyword=keyword,
        current_category=category,
        offers_filter=OFFERS_FILTER,
        visitor_stats=visitor_stats,
        seo=seo,
    )


@shop_bp.route("/about_us", methods=["GET"], endpoint='about_us')
def about_us():
    lang = g.current_language
    title = g.translations.get("About_Us", "About Us")
    if lang == "ar":
        desc = "تعرف على هاواري شوب — متجرك للمستلزمات المدرسية والمكتبية في مصر."
    else:
        desc = "Learn about HAWARY SHOP — your store for school and office supplies in Egypt."
    return render_template("about_us.html", seo=site_seo(lang, title=title, description=desc))


@shop_bp.route('/product/<int:product_id>', methods=["GET", "POST"], endpoint='product_page')
def product_page(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == "POST":
        product_size_id_selected = request.form.get("product_size_id")
        if product_size_id_selected:
            return redirect(url_for("product_page", product_id=product_id, product_size_id=product_size_id_selected))
        else:
            return redirect(url_for("product_page", product_id=product_id))

    product_size_id = request.args.get("product_size_id", type=int)
    selected_product_size = None
    current_available_quantity = 0

    if product_size_id:
        for size in product.sizes:
            if size.id == product_size_id:
                selected_product_size = size
                current_available_quantity = size.available_quantity
                break
        if not selected_product_size:
            flash(g.translations["selected_size_not_available"], "danger")
            return redirect(url_for("product_page", product_id=product_id))
    else:
        current_available_quantity = sum(size.available_quantity for size in product.sizes)

    if len(product.sizes) == 1 and not selected_product_size:
        return redirect(url_for(
            "product_page",
            product_id=product_id,
            product_size_id=product.sizes[0].id
        ))

    order = session.get("order", {})
    cart_key = f"{product_id}_{selected_product_size.id}" if selected_product_size else ''

    has_purchased = False
    if current_user.is_authenticated:
        delivered_orders = Order.query.filter_by(user_id=current_user.id, status='Delivered').all()
        for order_obj in delivered_orders:
            if any(item.product_id == product_id for item in order_obj.items):
                has_purchased = True
                break

    seo = build_product_seo(product, selected_product_size, g.current_language)

    return render_template(
        'product_page.html',
        product=product,
        order=order,
        cart_key=cart_key,
        selected_product_size=selected_product_size,
        current_available_quantity=current_available_quantity,
        has_purchased=has_purchased,
        seo=seo,
    )


@shop_bp.route("/test-time", endpoint='test_time')
def test_time():
    now = datetime.now(tz=ZoneInfo("UTC"))
    return render_template("test_time.html", now=now)


@shop_bp.route("/privacy-policy", endpoint='privacy_policy')
def privacy_policy():
    return _policy_page("privacy_policy.html", "Privacy_Policy", "privacy")


@shop_bp.route("/refund-policy", endpoint='refund_policy')
def refund_policy():
    return _policy_page("refund_policy.html", "Refund_Policy", "refund")


@shop_bp.route("/shipping-policy", endpoint='shipping_policy')
def shipping_policy():
    return _policy_page("shipping_policy.html", "Shipping_Policy", "shipping")


@shop_bp.route("/terms-and-conditions", endpoint='terms_and_conditions')
def terms_and_conditions():
    return _policy_page("terms_and_conditions.html", "Terms_and_Conditions", "terms")


def _policy_page(template_name, title_key, policy_kind):
    lang = g.current_language
    title = g.translations.get(title_key, title_key.replace("_", " "))
    descriptions_ar = {
        "privacy": "سياسة الخصوصية لموقع هاواري شوب.",
        "refund": "سياسة الاسترجاع والاسترداد في هاواري شوب.",
        "shipping": "سياسة الشحن والتوصيل لطلبات هاواري شوب.",
        "terms": "الشروط والأحكام لاستخدام متجر هاواري شوب.",
    }
    descriptions_en = {
        "privacy": "Privacy policy for HAWARY SHOP.",
        "refund": "Refund and return policy for HAWARY SHOP orders.",
        "shipping": "Shipping and delivery policy for HAWARY SHOP.",
        "terms": "Terms and conditions for using HAWARY SHOP.",
    }
    desc = (descriptions_ar if lang == "ar" else descriptions_en)[policy_kind]
    return render_template(template_name, seo=site_seo(lang, title=title, description=desc))


@shop_bp.route('/sitemap.xml', methods=['GET'], endpoint='sitemap')
def sitemap():
    pages = []
    current_date = datetime.now(ZoneInfo("UTC")).date()
    static_pages = [
        ('home', '1.0'),
        ('about_us', '0.6'),
        ('privacy_policy', '0.4'),
        ('refund_policy', '0.4'),
        ('shipping_policy', '0.4'),
        ('terms_and_conditions', '0.4'),
    ]
    for page, priority in static_pages:
        url = url_for(page, _external=True)
        pages.append({'loc': url, 'lastmod': current_date, 'priority': priority})
    products = Product.query.order_by(Product.id).all()
    for product in products:
        kwargs = {'product_id': product.id, '_external': True}
        if len(product.sizes) == 1:
            kwargs['product_size_id'] = product.sizes[0].id
        url = url_for('product_page', **kwargs)
        pages.append({'loc': url, 'lastmod': current_date, 'priority': '0.7'})
    sitemap_xml = render_template("sitemap_template.xml", pages=pages)
    return Response(sitemap_xml, mimetype='application/xml')


@shop_bp.route('/robots.txt', endpoint='robots')
def robots():
    return send_from_directory(current_app.static_folder, 'robots.txt')
