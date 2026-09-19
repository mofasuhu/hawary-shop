from datetime import datetime
from zoneinfo import ZoneInfo
from flask import g

cairo_tz = ZoneInfo("Africa/Cairo")


def product_translate_process(text: str):
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


def translation_key(text: str):
    translation_key_text = (
        text.replace(" ", "_")
        .replace(".", "")
        .replace("'", "")
        .replace(":", "")
        .replace("!", "")
        .replace(",", "")
        .replace("-", "_")
        .replace("&", "and")
    )
    return translation_key_text.lower()


def tz_aware_to_cairo_time(dt: datetime):
    if dt:
        return dt.astimezone(cairo_tz)
    return None


def to_cairo_time(dt: datetime):
    if dt:
        if dt.tzinfo is not None:
            return dt.astimezone(cairo_tz)
        dt_utc = dt.replace(tzinfo=ZoneInfo("UTC"))
        return dt_utc.astimezone(cairo_tz)
    return None


def datetimeformat(value, format='%Y-%m-%d %I:%M:%S %p'):
    if value:
        formatted_date = value.strftime(format)
        if g.current_language == 'ar':
            formatted_date = formatted_date.replace('AM', g.translations['AM']).replace('PM', g.translations['PM'])
        return formatted_date
    return ''


def dateformat(value, format='%Y-%m-%d'):
    if value:
        return value.strftime(format)
    return ''


def contains_arabic(text):
    import re
    arabic_re = re.compile("[\u0600-\u06FF]")
    return bool(arabic_re.search(text))


def register_filters(app):
    """Register all Jinja2 template filters with the app."""
    app.jinja_env.filters['product_translate_process'] = product_translate_process
    app.jinja_env.filters['translation_key'] = translation_key
    app.jinja_env.filters['tz_aware_to_cairo_time'] = tz_aware_to_cairo_time
    app.jinja_env.filters['to_cairo_time'] = to_cairo_time
    app.jinja_env.filters['datetimeformat'] = datetimeformat
    app.jinja_env.filters['dateformat'] = dateformat
    app.jinja_env.filters['contains_arabic'] = contains_arabic
