# Hawary Shop

Production-oriented **bilingual (Arabic / English)** e-commerce platform built with **Python, Flask, PostgreSQL, and Gunicorn**.

| | |
|---|---|
| **Live demo** | [mist-app.onrender.com](https://mist-app.onrender.com/) |
| **Portfolio** | [mofasuhu.github.io](https://mofasuhu.github.io/) |
| **Author** | [Muhammad Farouk](https://www.linkedin.com/in/muhammadfarouk) |

> This public repository is a **sanitized portfolio copy** of the Hawary Shop codebase. Production hosting (Render), live Paymob credentials, and private ops data stay in a **separate private** repo and are **not** linked here.

---

---

## Live product screenshots

Captured from the live demo ([mist-app.onrender.com](https://mist-app.onrender.com/)).

### Storefront (public)

| | |
|---|---|
| Home (Arabic / RTL) | Home (English) |
| ![Home AR](docs/screenshots/01-home-ar.png) | ![Home EN](docs/screenshots/02-home-en.png) |
| Product detail | About |
| ![Product](docs/screenshots/03-product.png) | ![About](docs/screenshots/04-about.png) |

### Client account

| | |
|---|---|
| Logged-in home | Wishlist |
| ![Client home](docs/screenshots/05-client-home.png) | ![Wishlist](docs/screenshots/06-client-wishlist.png) |
| Orders | Cart |
| ![Orders](docs/screenshots/07-client-orders.png) | ![Cart](docs/screenshots/08-client-cart.png) |

![Client profile (title crop)](docs/screenshots/09-client-profile.png)

### Product reviews, offers & checkout

| | |
|---|---|
| Verified product reviews | Offers filter |
| ![Reviews](docs/screenshots/19-product-reviews.png) | ![Offers](docs/screenshots/20-offers.png) |
| Checkout payment choice (Bank Card / COD) | Product detail (Arabic) |
| ![Checkout](docs/screenshots/21-checkout.png) | ![Product AR](docs/screenshots/22-bilingual-product-ar.png) |

### Admin

| | |
|---|---|
| Admin home + visitor stats | Orders management |
| ![Admin home](docs/screenshots/10-admin-home.png) | ![Admin orders](docs/screenshots/11-admin-orders.png) |
| Catalog / product update | Transactions |
| ![Products](docs/screenshots/12-admin-products.png) | ![Transactions](docs/screenshots/13-admin-transactions.png) |
| Wishlists oversight | Accounts |
| ![Wishlists](docs/screenshots/14-admin-wishlists.png) | ![Accounts](docs/screenshots/15-admin-accounts.png) |

### Superadmin

| | |
|---|---|
| Superadmin home | Create admin |
| ![SA home](docs/screenshots/16-superadmin-home.png) | ![Create admin](docs/screenshots/17-superadmin-create-admin.png) |

![Translation management](docs/screenshots/18-superadmin-translation.png)

## Why this project matters

Hawary Shop is not a tutorial cart — it is a full storefront + admin operations system with:

- Real payment integration (**Paymob**) including **HMAC-verified webhooks**, failed-transaction logging, and **refunds**
- Egypt-specific **governorate delivery** with **dimensional-weight** shipping factors
- **DB-driven i18n** (AR default + EN) with **RTL** layout and Cairo / Inter typography
- Hardened auth (**scrypt**, login lockout, admin **TOTP 2FA**, rate limits, CSRF, CSP)
- Recruiter-visible **SEO** (Open Graph, Twitter cards, Product JSON-LD, sitemap, robots.txt)
- Automated **pytest** coverage for the highest-risk paths (auth, cart, COD checkout, delivery math, SEO, mail, env validation)

---

## Feature overview (implemented)

### Storefront & catalog
- Product catalog with bilingual fields (name, category, ingredients, gender, description)
- Up to **10** product images per item (Cloudinary-backed uploads in admin)
- Size variants with price, stock, weight, and dimensions
- Discount percent per product; “offers” style browsing supported in shop routes
- Product detail pages with cart integration and size API (`/api/product/<id>/sizes`)

### Cart, wishlist, reviews, promos
- Session cart synchronized to **`UserCart`** in the database on login / after-request
- Quantity update, increment/decrement, remove, clear — with **stock caps**
- Wishlist stored as product ID lists per user; admin can oversee wishlists
- Reviews: **only verified buyers** who have a **Delivered** order containing the product (upsert by user+product, rating 1–5)
- Single-use **promo codes** (percent off); preview in cart; marked used on successful order completion
- Product discount applied first, then promo percent (covered by tests)

### Checkout & payments
- **Cash on Delivery (COD)** path: creates order + line items, decrements stock, applies promo, clears cart; payment status *Pay on Delivery*
- **Bank card via Paymob Intention API** (`accept.paymob.com`): creates temporary order payload, redirects to unified checkout; **order finalization is webhook-driven**
- Checkout requires a **covered** governorate (`is_covered`)
- Stock validation before commit
- Redirect handler is UX-only; webhook is source of truth for paid orders

### Paymob reliability & money movement
- Webhook authenticity via **HMAC-SHA512** over an ordered key set (including nested Paymob fields), compared with `hmac.compare_digest`
- Idempotent processing when a `Transaction` already exists for the Paymob transaction id
- Amount mismatch / void / error paths record **`FailedTransaction`** (raw payload retained for ops) and mark temp checkout data processed
- **Refunds** via Paymob void/refund API; tracks `refunded_amount_cents` / `is_refunded`; updates order payment status; admin can refund; cancel/edit flows can trigger auto-refund for card-paid orders

### Delivery (Egypt)
- Per-governorate **`GovernorateDeliveryFee`**: `base_fee`, `per_kg_rate`, `is_covered`
- Per size **`delivery_factor`** auto-calculated as  
  `max(weight_kg, (L × W × H) / 5000, 0.1)` (dimensional weight factor **5000**)
- Fee formula: `base_fee + Σ(qty × delivery_factor) × per_kg_rate` (integer, clamped ≥ 0)
- Uncovered / unknown governorates blocked or flagged at cart/checkout

### Customer account
- Signup / login / logout with email confirmation (timed serializer) and password reset (DB token, short expiry, HTML email)
- Strong password rules (length, upper/lower/digit/special, no spaces)
- Optional **Google OAuth** (Authlib); new Google users complete profile before shopping
- Order history, client-side order view/edit/cancel where allowed by status
- Language cookie `en` | `ar` (default **Arabic**)

### Admin & operations
- Role model: client / admin / **superadmin**
- **Product CRUD** + size management; Cloudinary uploads with type whitelist; block delete when product appears on orders
- **Orders**: list/edit (Pending/Preparing), add line items, status updates with **status emails**, delete (superadmin), refunds
- **Accounts**: list/download, edit, create admin, delete client/admin (superadmin)
- **Wishlists** oversight
- **Reports**: transaction / product exports (xlsx/CSV/JSON), promo generation (8-char codes) + CSV download
- Optional DB dump download for admins (uses configured `DB_*` / tooling — secrets via env only)
- Live **visitor** stats on the shop home for authenticated admins (`VisitorLog`)

### Internationalization (i18n)
- Translations stored in Postgres (`key`, `value_en`, `value_ar`) with case-insensitive lookup helpers
- Request hooks load `g.translations` / `g.current_language` for templates
- RTL class + Arabic-aware field direction in `base.html`
- Fonts: **Cairo**, **Inter**, and Noto Naskh Arabic for readable bilingual UI

---

## Security (defense in depth)

| Control | Implementation |
|--------|----------------|
| Password hashing | Werkzeug **scrypt** |
| Login lockout | After **7** failed attempts → lock **15 minutes** |
| Rate limiting | Flask-Limiter: login **10/min**, signup **20/hour**, plus global defaults |
| Admin 2FA | **TOTP** (`pyotp` + QR); admins without a secret forced through setup; verify step after password/Google |
| CSRF | Flask-WTF CSRFProtect (payment webhook explicitly exempt) |
| CSP / HTTPS | Flask-Talisman CSP; HTTPS + secure cookies when `FLASK_ENV=production` **and** `RENDER=1` |
| Cookies | HttpOnly; SameSite `None`+Secure in prod, else `Lax` |
| Uploads | Whitelist **`png/jpg/jpeg/webp`** + `secure_filename` + Cloudinary transforms |
| Payments | HMAC verification; failed txn logging; no secrets in repo |
| CORS | Allowlist for `hawary.shop` / `www.hawary.shop` |
| URL hygiene | Production HTTPS apex redirect (strip www / trailing slash) |
| Timing | Short delay on failed/unconfirmed auth paths |

Secrets are loaded from environment variables and validated at startup (`app/env_validation.py`). This public copy ships **`.env.example` only**.

---

## SEO & discoverability

- Shared helpers in `app/utils/seo.py`: truncation, absolute image URLs, **product SEO** (title/description with EGP, Open Graph product fields, availability)
- **Product JSON-LD** (`Product` + `Offer` / `AggregateOffer` + `AggregateRating` when reviews exist)
- Site-wide defaults with locales `ar_EG` / `en_EG`
- Templates emit meta description, **Open Graph**, and **Twitter** `summary_large_image`
- Dynamic **`/sitemap.xml`** (home / about / policies / products with priorities)
- **`robots.txt`**: allow public pages; disallow auth, cart, checkout, wishlist, admin, and similar private paths; sitemap pointer for production domain

Covered by `tests/test_seo.py`.

---

## Architecture

```
Browser (AR/EN, RTL)
    │
    ▼
Flask app factory (create_app)
    ├── Blueprints: auth, shop, cart, checkout, customer, admin*, api
    ├── Services: payment (Paymob), delivery, email (async)
    ├── Models: users, catalog, orders, payments, delivery fees, translations, analytics
    ├── Extensions: SQLAlchemy, Migrate, Login, Mail, Limiter, CSRF, Talisman, OAuth
    └── Postgres
            ▲
Paymob webhooks ── HMAC verify ──► checkout + Transaction / FailedTransaction
```

**Entry points**
- Local: `python app.py` (loads `.env` / `Local.env`)
- Production-style: `gunicorn wsgi:application` (`Procfile`)

**Notable engineering details**
- Application factory with strict **environment validation** before boot
- Bare `url_for` endpoint remap for legacy template compatibility
- Cart persistence across anonymous → authenticated sessions
- Temp checkout payload (`TempOrderData`) bridges Paymob redirect/webhook continuity
- Hybrid money fields on transactions (e.g. net amount in cents) for accurate settlement/refund tracking

---

## Tech stack

| Layer | Choices |
|------|---------|
| Language | Python 3 |
| Web | Flask, Flask-Login, Flask-WTF, Flask-CORS |
| ORM / migrations | Flask-SQLAlchemy, Flask-Migrate (Alembic) |
| DB | PostgreSQL (SQLite in-memory for tests) |
| Auth extras | Authlib (Google), pyotp + qrcode (admin 2FA) |
| Payments | Paymob Intention + Acceptance APIs |
| Media | Cloudinary |
| Security | Flask-Talisman, Flask-Limiter, scrypt, CSRF |
| Email | Flask-Mail, async send helper |
| Tests | pytest |
| Serve | Gunicorn / Render-oriented config |

---

## Test suite

| Module | Focus |
|--------|--------|
| `tests/test_auth.py` | Signup → unconfirmed user + confirmation mail; login success/failure; email confirm token |
| `tests/test_cart.py` | Add to cart; over-stock rejection; promo after product discount |
| `tests/test_checkout.py` | COD order creation + stock decrement; empty cart; below-minimum guard |
| `tests/test_delivery.py` | Fee math; unknown governorate → zero fees / non-success |
| `tests/test_seo.py` | Product/site SEO fields; OG/Twitter; JSON-LD; sitemap; robots disallow rules |
| `tests/test_email_async.py` | Async mail queue for order / reset / confirm |
| `tests/test_env_validation.py` | Required secrets; production Paymob requirements; skip flag |

```bash
pip install -r requirements.txt
SKIP_ENV_VALIDATION=1 pytest -q
```

---

## Quick start (local / portfolio)

```bash
git clone https://github.com/mofasuhu/hawary-shop.git
cd hawary-shop
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Configure local Postgres + sandbox Paymob/Cloudinary/Mail values only
flask db upgrade            # or your usual migration workflow
python app.py               # or: gunicorn wsgi:application
```

**Do not** put production Paymob, Cloudinary, Google, or database credentials in this public project.

---

## Repository layout

```
app/                 Factory, config, models, routes, services, SEO/auth utilities
migrations/          Alembic history (incl. 2FA / lockout)
templates/           Jinja2 storefront + admin
static/              CSS/JS, icons, robots.txt, product media samples
tests/               pytest suite + fixtures
scripts/             HMAC helpers, DB backup/restore, fee seeding, route parity checks
.env.example         Environment variable names (no secrets)
wsgi.py / Procfile   Production process entry
README.md            This document
```

---

## What this public copy intentionally omits

- Real `.env` / Render secrets
- Database dumps and private ops folders
- Production-only credentials and internal support tooling data

The commercial deployment and private source of truth remain separate from this portfolio mirror.

---

## License / contact

Portfolio showcase by **Muhammad Farouk**.  
Email: [mofasuhu@gmail.com](mailto:mofasuhu@gmail.com) · [LinkedIn](https://www.linkedin.com/in/muhammadfarouk) · [GitHub](https://github.com/mofasuhu)
