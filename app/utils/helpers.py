import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from collections import defaultdict
from flask import g, session
from flask_login import current_user
from app.extensions import db
from app.models.product import Product, ProductSize
from app.models.translation import Translation
from app.models.user import UserCart

cairo_tz = ZoneInfo("Africa/Cairo")


def contains_arabic(text):
    arabic_re = re.compile("[\u0600-\u06FF]")
    return bool(arabic_re.search(text))


def today():
    return datetime.now(cairo_tz).strftime("%Y-%m-%d %I-%M-%S %p")


def mydtfmt(datetimestr):
    return datetime.strptime(datetimestr, "%Y-%m-%d")


def end_date_correction(dt):
    return dt + timedelta(days=1)


def get_product_data(product_name):
    if g.current_language == 'ar':
        product = Product.query.filter_by(name_ar=product_name).first()
    else:
        product = Product.query.filter_by(name_en=product_name).first()
    return product


def product_translate_process(text: str):
    """Process text into a translation key for products."""
    product_processed_text = (
        text.replace(" ", "_")
        .replace(".", "")
        .replace("'", "")
        .replace(":", "")
        .replace("!", "")
        .replace(",", "")
        .replace("-", "_")
        .replace("&", "and")
    )
    return f"product_{product_processed_text}_product"


def create_translation_item(value_en, value_ar):
    key = product_translate_process(value_en)
    existing_translation = Translation.query.filter_by(key=key).first()
    if existing_translation:
        existing_translation.value_en = value_en
        existing_translation.value_ar = value_ar
    else:
        new_translation = Translation(key=key, value_en=value_en, value_ar=value_ar)
        db.session.add(new_translation)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()


def add_product_translations(product):
    create_translation_item(product.name_en, product.name_ar)
    create_translation_item(product.category_en, product.category_ar)
    create_translation_item(product.ingredients_en, product.ingredients_ar)
    create_translation_item(product.gender_en, product.gender_ar)
    for size in product.sizes:
        create_translation_item(size.size_en, size.size_ar)
    create_translation_item(product.description_en, product.description_ar)


# Reserved category query value for home-page "Offers" filter (not a real Product.category_en).
OFFERS_FILTER = "__offers__"


def get_unique_values(attribute_type):
    if attribute_type == 'category':
        results = Product.query.with_entities(Product.category_en).distinct().all()
        return list(set([result[0] for result in results if result[0]]))
    elif attribute_type == 'gender':
        results = Product.query.with_entities(Product.gender_en).distinct().all()
        return list(set([result[0] for result in results if result[0]]))
    elif attribute_type == 'product_size':
        results = ProductSize.query.with_entities(ProductSize.size_en).distinct().all()
        return list(set([result[0] for result in results if result[0]]))
    return []


def search_and_filter(keyword, category):
    query = Product.query

    if keyword:
        search_term = f"%{keyword}%"
        query = query.filter(
            (
                Product.name_en.ilike(search_term) |
                Product.name_ar.ilike(search_term) |
                Product.category_en.ilike(search_term) |
                Product.category_ar.ilike(search_term) |
                Product.ingredients_en.ilike(search_term) |
                Product.ingredients_ar.ilike(search_term) |
                Product.description_en.ilike(search_term) |
                Product.description_ar.ilike(search_term)
            )
        )

    if category == OFFERS_FILTER:
        query = query.filter(Product.discount_percent > 0)
    elif category:
        query = query.filter(Product.category_en == category)

    products = query.order_by(Product.category_en, Product.name_en).all()
    category_map = defaultdict(list)
    for p in products:
        category_map[p.category_en].append(p)

    result = []
    more = True
    round_index = 0
    while more:
        more = False
        for cat_key in sorted(category_map.keys()):
            cat_products = category_map[cat_key]
            if round_index < len(cat_products):
                result.append(cat_products[round_index])
                more = True
        round_index += 1

    return result


def get_cart_count():
    """Returns the count of items in the cart."""
    order = session.get("order", {})
    return sum(item['quantity'] for item in order.values()) if order else 0


def save_cart_to_db():
    """
    Saves the current session cart to the database for the logged-in user.
    """
    if not current_user.is_authenticated:
        return

    cart_data = session.get("order")
    user_cart = UserCart.query.filter_by(user_id=current_user.id).first()

    if cart_data:
        if user_cart:
            user_cart.cart_data = cart_data
        else:
            user_cart = UserCart(user_id=current_user.id, cart_data=cart_data)
            db.session.add(user_cart)
    elif user_cart:
        db.session.delete(user_cart)

    db.session.commit()
