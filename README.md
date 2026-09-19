# Hawary Shop

Production-ready **bilingual** (Arabic/English) e-commerce platform built with **Python, Flask, PostgreSQL, and Gunicorn**.

> **Live demo:** [mist-app.onrender.com](https://mist-app.onrender.com/)  
> **Portfolio site:** [mofasuhu.github.io](https://mofasuhu.github.io/)

This public repository is a **sanitized portfolio copy** of the Hawary Shop codebase for hiring review. The production app (Render hosting, live Paymob, real credentials) remains in a **private** repo and is not linked here.

## Highlights

- Full shopping flow: browse → image gallery → cart → promo codes → **Paymob** or cash-on-delivery → order tracking with status emails
- Per-governorate delivery fees with dimensional-weight calculation
- Wishlist, verified buyer reviews/ratings, DB-driven AR/EN translations (RTL + Cairo/Inter typography)
- Admin sidebar: CRUD, reports, promo codes, translations, wishlist oversight, **TOTP 2FA**
- Paymob webhooks with **HMAC verification**, refunds, failed-transaction logging
- Security: CSP (Flask-Talisman), login lockout, scrypt password hashing, upload whitelist
- SEO: per-page meta, Open Graph, Twitter cards, Product JSON-LD, sitemap / robots.txt
- Automated tests (`pytest`) covering auth, cart, checkout, SEO, and email paths

## Stack

| Layer | Tech |
|------|------|
| Backend | Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF |
| DB | PostgreSQL |
| Payments | Paymob (HMAC-verified webhooks) |
| Media | Cloudinary |
| Auth extras | Google OAuth (optional), TOTP 2FA for admin |
| Deploy | Gunicorn / Render (production private) |

## Quick start (local)

```bash
git clone https://github.com/mofasuhu/hawary-shop.git
cd hawary-shop
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env with local Postgres + sandbox keys
flask db upgrade   # or your usual migration flow
python app.py      # or: gunicorn wsgi:app
```

Use **sandbox/test** Paymob and Cloudinary credentials only. Do not put production secrets in `.env` for this public project.

## Project layout

```
app/           Application factory, models, routes, services (payments, email, delivery)
migrations/    Alembic / Flask-Migrate history
templates/     Jinja2 (shop + admin)
static/        CSS/JS/assets
tests/         pytest suite
scripts/       Dev/ops helpers
.env.example   Required environment variable names (no secrets)
```

## Security note

- No `.env`, database dumps, or production credentials are included.
- Payment and OAuth integrations read secrets from environment variables.
- If you fork this repo, rotate any keys you add and keep them out of git.

## License / attribution

Portfolio showcase by [Muhammad Farouk](https://mofasuhu.github.io/). Live commercial deployment is separate from this public mirror.

## Contact

mofasuhu@gmail.com · [LinkedIn](https://www.linkedin.com/in/muhammadfarouk)
