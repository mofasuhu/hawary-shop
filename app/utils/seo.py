"""SEO helpers: meta tags, Open Graph, and Product JSON-LD."""
import re
from html import unescape
from flask import url_for

BRAND_NAME = "Hawary Shop"
DEFAULT_OG_IMAGE = "web-app-manifest-512x512_v3.png"


def strip_and_truncate(text, max_len=160):
    """Plain text for meta descriptions from HTML or long copy."""
    if not text:
        return ""
    plain = unescape(re.sub(r"<[^>]+>", " ", str(text)))
    plain = re.sub(r"\s+", " ", plain).strip()
    if len(plain) <= max_len:
        return plain
    return plain[: max_len - 3].rstrip() + "..."


def absolute_image_url(image_path):
    """Absolute HTTPS URL for product or static image."""
    if not image_path:
        return url_for("static", filename=DEFAULT_OG_IMAGE, _external=True)
    if image_path.startswith("http"):
        return image_path
    return url_for("static", filename=image_path, _external=True)


def _discounted_unit_price(product, product_size):
    discount = product.discount_percent or 0
    return round(product_size.price * (1 - discount / 100), 2)


def _product_labels(product, lang):
    if lang == "ar":
        return product.name_ar, product.category_ar
    return product.name_en, product.category_en


def _price_display(product, selected_product_size):
    """Return (low, high, single_display) discounted prices in EGP."""
    sizes = [s for s in product.sizes if s.available_quantity > 0]
    if not sizes:
        sizes = list(product.sizes)
    if not sizes:
        return None, None, None

    discounted = [_discounted_unit_price(product, s) for s in sizes]
    low, high = min(discounted), max(discounted)

    if selected_product_size:
        return low, high, _discounted_unit_price(product, selected_product_size)
    if low == high:
        return low, high, low
    return low, high, None


def build_product_seo(product, selected_product_size, lang):
    """SEO context for product detail pages."""
    name, category = _product_labels(product, lang)
    description_html = product.description_ar if lang == "ar" else product.description_en
    description = strip_and_truncate(description_html, 160)

    low, high, single = _price_display(product, selected_product_size)
    egp = "جنيه" if lang == "ar" else "EGP"

    if single is not None:
        price_part = f"{single:.2f} {egp}"
    elif low is not None and high is not None:
        price_part = f"{low:.2f} – {high:.2f} {egp}"
    else:
        price_part = ""

    title = f"{name} | {category} | {price_part}" if price_part else f"{name} | {category}"
    if description and price_part:
        meta_desc = f"{name} — {category}. {price_part}. {description}"
    elif price_part:
        meta_desc = f"{name} — {category}. {price_part}."
    else:
        meta_desc = description or f"{name} — {category}."

    meta_desc = strip_and_truncate(meta_desc, 160)

    og_image = absolute_image_url(product.image_url)
    locale = "ar_EG" if lang == "ar" else "en_EG"

    in_stock = any(s.available_quantity > 0 for s in product.sizes)
    availability = "in stock" if in_stock else "out of stock"

    json_ld = _product_json_ld(
        product=product,
        lang=lang,
        name=name,
        description=description,
        image_url=og_image,
        low=low,
        high=high,
        single=single,
        in_stock=in_stock,
    )

    return {
        "title": title,
        "description": meta_desc,
        "og_title": name,
        "og_description": meta_desc,
        "og_image": og_image,
        "og_type": "product",
        "og_locale": locale,
        "og_price_amount": f"{single:.2f}" if single is not None else (f"{low:.2f}" if low is not None else None),
        "og_price_currency": "EGP",
        "availability": availability,
        "json_ld": json_ld,
    }


def _product_json_ld(product, lang, name, description, image_url, low, high, single, in_stock):
    images = []
    for url in (
        product.image_url,
        product.image_url_2,
        product.image_url_3,
        product.image_url_4,
        product.image_url_5,
    ):
        if url:
            images.append(absolute_image_url(url))

    data = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": name,
        "description": description,
        "image": images or [image_url],
        "brand": {"@type": "Brand", "name": BRAND_NAME},
    }

    availability = "https://schema.org/InStock" if in_stock else "https://schema.org/OutOfStock"
    if single is not None:
        data["offers"] = {
            "@type": "Offer",
            "priceCurrency": "EGP",
            "price": f"{single:.2f}",
            "availability": availability,
            "url": url_for("product_page", product_id=product.id, _external=True),
        }
    elif low is not None and high is not None:
        data["offers"] = {
            "@type": "AggregateOffer",
            "priceCurrency": "EGP",
            "lowPrice": f"{low:.2f}",
            "highPrice": f"{high:.2f}",
            "availability": availability,
            "offerCount": len(product.sizes),
        }

    reviews = list(product.reviews) if product.reviews else []
    if reviews:
        ratings = [r.rating for r in reviews if r.rating]
        if ratings:
            data["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": round(sum(ratings) / len(ratings), 1),
                "reviewCount": len(ratings),
            }

    return data


def site_seo(lang, title=None, description=None):
    """Default SEO for public static pages."""
    if lang == "ar":
        default_title = "هاواري شوب | متجرك اليومي"
        default_desc = "تسوق منتجات عالية الجودة من هاواري شوب — توصيل داخل مصر."
    else:
        default_title = "HAWARY SHOP | Your Everyday Store"
        default_desc = "Shop quality products at HAWARY SHOP — delivery across Egypt."

    return {
        "title": title or default_title,
        "description": description or default_desc,
        "og_title": title or default_title,
        "og_description": description or default_desc,
        "og_image": url_for("static", filename=DEFAULT_OG_IMAGE, _external=True),
        "og_type": "website",
        "og_locale": "ar_EG" if lang == "ar" else "en_EG",
    }
