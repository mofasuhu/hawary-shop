"""Pytest fixtures for Hawary Shop."""
import os

os.environ.setdefault("SKIP_ENV_VALIDATION", "1")
os.environ["FLASK_ENV"] = "development"
os.environ.pop("RENDER", None)
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("MAIL_SERVER", "smtp.test.local")
os.environ.setdefault("MAIL_PORT", "587")
os.environ.setdefault("MAIL_USERNAME", "test@example.com")
os.environ.setdefault("MAIL_PASSWORD", "test-mail-password")
os.environ.setdefault("MAIL_DEFAULT_SENDER", "test@example.com")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-google-client-id")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-google-client-secret")
os.environ.setdefault("CLOUDINARY_CLOUD_NAME", "test-cloud")
os.environ.setdefault("CLOUDINARY_API_KEY", "test-key")
os.environ.setdefault("CLOUDINARY_API_SECRET", "test-secret")
os.environ.setdefault("PAYMOB_SECRET_KEY", "test-paymob-secret")
os.environ.setdefault("PAYMOB_PUBLIC_KEY", "test-paymob-public")
os.environ.setdefault("PAYMOB_INTEGRATION_ID", "123456")
os.environ.setdefault("PAYMOB_HMAC_SECRET", "test-hmac-secret")
os.environ.setdefault("FIRST_SUPERADMIN_MAIL", "admin@test.local")
os.environ.setdefault("FIRST_SUPERADMIN_PASSWORD", "AdminPass1!")
os.environ.setdefault("FIRST_SUPERADMIN_FULLNAME", "Test Admin")
os.environ.setdefault("FIRST_SUPERADMIN_MOBILE", "01000000000")
os.environ.setdefault("FIRST_SUPERADMIN_ADDRESS", "Test Address")
os.environ.setdefault("FIRST_SUPERADMIN_AREA", "cairo")

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models.user import User, UserCart
from app.models.product import Product, ProductSize
from app.models.delivery import GovernorateDeliveryFee
from app.models.translation import Translation

TEST_PASSWORD = "TestPass1!"


def persist_user_cart(app, user_id, order_data):
    """Mirror session cart to UserCart so load_cart_from_db does not clear it."""
    with app.app_context():
        cart = UserCart.query.filter_by(user_id=user_id).first()
        if cart:
            cart.cart_data = order_data
        else:
            cart = UserCart(user_id=user_id, cart_data=order_data)
            db.session.add(cart)
        db.session.commit()

TRANSLATION_SEEDS = {
    "Invalid_email_address_format": ("Invalid email", "بريد غير صالح"),
    "Password_length_error": ("Password too short", "كلمة مرور قصيرة"),
    "Password_spaces_error": ("No spaces in password", "لا مسافات"),
    "Password_uppercase_error": ("Need uppercase", "حرف كبير"),
    "Password_lowercase_error": ("Need lowercase", "حرف صغير"),
    "Password_number_error": ("Need number", "رقم"),
    "Password_special_char_error": ("Need special char", "رمز"),
    "login_unsuccessful_please_check_username_and_password": (
        "Invalid credentials",
        "بيانات خاطئة",
    ),
    "your_email_hasnt_confirmed": ("Email not confirmed", "لم يؤكد"),
    "a_confirmation_email_has_been_sent_please_check_your_email": (
        "Check your email",
        "تحقق من بريدك",
    ),
    "Confirm_Your_Email": ("Confirm your email", "أكد بريدك"),
    "Reset_Your_Password": ("Reset your password", "إعادة تعيين كلمة المرور"),
    "username_already_exists_please_choose_a_different_one": (
        "Username exists",
        "المستخدم موجود",
    ),
    "your_account_has_been_confirmed_please_log_in": (
        "Account confirmed",
        "تم التأكيد",
    ),
    "the_confirmation_link_is_invalid_or_has_expired": (
        "Invalid link",
        "رابط غير صالح",
    ),
    "invalid_quantity_format": ("Invalid quantity", "كمية غير صالحة"),
    "missing_product_or_size": ("Missing product", "منتج مفقود"),
    "quantity_cannot_be_negative": ("Negative quantity", "كمية سالبة"),
    "cannot_add_more_than_available": ("Not enough stock", "لا يوجد مخزون"),
    "product_or_size_not_found_for_id": ("Not found", "غير موجود"),
    "No_Items_In_Order": ("No items", "لا عناصر"),
    "invalid_or_expired_promo_code": ("Invalid promo", "كود غير صالح"),
    "no_items_in_order": ("No items in order", "لا عناصر في الطلب"),
    "please_select_a_payment_method": ("Select payment", "اختر الدفع"),
    "minimum_order_amount_is_100": (
        "Minimum order is {min_order_amount}",
        "الحد الأدنى {min_order_amount}",
    ),
    "delivery_not_available_for_this_area_no_zone": (
        "No delivery zone",
        "لا توصيل",
    ),
    "delivery_fees_not_configured_for_governorate": (
        "Fees not configured for {area}",
        "رسوم غير مهيأة",
    ),
    "product_size_not_found_for_delivery_calc": (
        "Size not found for delivery",
        "مقاس غير موجود",
    ),
    "Order_sent_successfully_with_total": (
        "Order sent. Total: {total_price}",
        "تم الطلب: {total_price}",
    ),
    "invalid_item_id_in_the_cart_please_clear_cart_and_try_again": (
        "Invalid cart item",
        "عنصر غير صالح",
    ),
    "product_or_size_not_found_for_one_item_please_clear_cart_and_try_again": (
        "Product not found",
        "منتج غير موجود",
    ),
    "payment_processing_error_session_lost": (
        "Payment error",
        "خطأ دفع",
    ),
    "Delivery_Fees": ("Delivery Fees", "رسوم التوصيل"),
    "oops_cash_on_delivery_up_to_5000": (
        "COD max {max_on_delivery_amount}",
        "حد الدفع عند الاستلام",
    ),
}


@pytest.fixture
def app():
    application = create_app()
    application.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        WTF_CSRF_ENABLED=False,
        CACHE_TYPE="NullCache",
    )
    yield application


@pytest.fixture
def _db(app):
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


@pytest.fixture
def seed_translations(app, _db):
    with app.app_context():
        for key, (value_en, value_ar) in TRANSLATION_SEEDS.items():
            _db.session.add(
                Translation(key=key, value_en=value_en, value_ar=value_ar)
            )
        _db.session.commit()


@pytest.fixture
def client(app, _db, seed_translations):
    return app.test_client()


@pytest.fixture
def catalog(app, _db):
    """Product, size, and cairo delivery fee for cart/checkout tests."""
    with app.app_context():
        product = Product(
            name_en="Test Product",
            name_ar="منتج تجريبي",
            category_en="Test",
            category_ar="تجريبي",
            ingredients_en="N/A",
            ingredients_ar="N/A",
            gender_en="Unisex",
            gender_ar="للجميع",
            description_en="Test",
            description_ar="تجريبي",
            image_url="test.jpg",
            discount_percent=10.0,
        )
        _db.session.add(product)
        _db.session.flush()

        size = ProductSize(
            product_id=product.id,
            size_en="M",
            size_ar="وسط",
            price=100.0,
            available_quantity=10,
            weight_kg=1.0,
            length_cm=10.0,
            width_cm=10.0,
            height_cm=10.0,
            delivery_factor=2.0,
        )
        _db.session.add(size)

        _db.session.add(
            GovernorateDeliveryFee(
                governorate_name="cairo",
                base_fee=50.0,
                per_kg_rate=5.5,
                is_covered=True,
            )
        )
        _db.session.commit()

        return {
            "product_id": product.id,
            "size_id": size.id,
            "price": size.price,
            "discount_percent": product.discount_percent,
            "name_en": product.name_en,
            "name_ar": product.name_ar,
            "size_en": size.size_en,
            "size_ar": size.size_ar,
        }


@pytest.fixture
def auth_user(app, _db):
    with app.app_context():
        user = User(
            username="client@test.local",
            password=generate_password_hash(TEST_PASSWORD, method="scrypt"),
            role="client",
            confirmed=True,
            full_name="Test Client",
            mobile="01012345678",
            address="123 Test Street",
            area="cairo",
        )
        _db.session.add(user)
        _db.session.commit()
        return {"id": user.id, "username": user.username}


@pytest.fixture
def auth_client(client, auth_user):
    response = client.post(
        "/login",
        data={"username": auth_user["username"], "password": TEST_PASSWORD},
        follow_redirects=False,
    )
    assert response.status_code in (301, 302, 200)
    return client
