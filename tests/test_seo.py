"""SEO helpers and public page markup."""

from app.extensions import db
from app.utils.seo import (
    build_product_seo,
    site_seo,
    strip_and_truncate,
)


def test_strip_and_truncate_strips_html_and_truncates():
    html = "<p>Hello <strong>world</strong> " + "x" * 200 + "</p>"
    result = strip_and_truncate(html, 50)
    assert "<" not in result
    assert result.endswith("...")
    assert len(result) <= 50


def test_build_product_seo_includes_price_and_json_ld(app, catalog):
    with app.test_request_context("/"):
        from app.models.product import Product, ProductSize

        product = db.session.get(Product, catalog["product_id"])
        size = db.session.get(ProductSize, catalog["size_id"])
        seo = build_product_seo(product, size, "en")

    assert catalog["name_en"] in seo["title"]
    assert "EGP" in seo["title"] or "EGP" in seo["description"]
    assert seo["og_type"] == "product"
    assert seo["og_price_currency"] == "EGP"
    assert seo["json_ld"]["@type"] == "Product"
    assert seo["json_ld"]["offers"]["priceCurrency"] == "EGP"


def test_site_seo_defaults_by_language(app):
    with app.test_request_context("/"):
        en = site_seo("en", title="About", description="About us")
        ar = site_seo("ar")

    assert en["title"] == "About"
    assert en["og_locale"] == "en_EG"
    assert ar["og_locale"] == "ar_EG"
    assert "512x512" in en["og_image"]


def test_home_page_has_meta_description(client, catalog):
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert '<meta name="description"' in html
    assert "og:title" in html
    assert "twitter:card" in html


def test_product_page_has_json_ld_and_og_price(client, catalog):
    pid = catalog["product_id"]
    sid = catalog["size_id"]
    response = client.get(f"/product/{pid}?product_size_id={sid}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "application/ld+json" in html
    assert "og:price:amount" in html or "product:price:amount" in html
    assert catalog["name_ar"] in html or catalog["name_en"] in html


def test_sitemap_includes_priorities_and_products(client, catalog):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    xml = response.get_data(as_text=True)
    assert "<priority>1.0</priority>" in xml
    assert f"/product/{catalog['product_id']}" in xml
    assert "product_size_id" in xml


def test_robots_disallows_wishlist(client):
    response = client.get("/robots.txt")
    assert response.status_code == 200
    assert "Disallow: /wishlist" in response.get_data(as_text=True)
