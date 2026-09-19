import time
import base64
from io import BytesIO
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pyotp
import qrcode
from qrcode.image.pil import PilImage
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, g, make_response, send_from_directory
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, limiter, oauth
import app.extensions as ext
from app.models.user import User
from app.models.translation import Translation
from app.config import EGYPT_GOVERNORATES
from app.services.email import generate_reset_token, send_password_reset_email, verify_reset_token, send_email_confirmation
from app.utils.validators import validate_username, validate_password
from app.utils.helpers import save_cart_to_db

auth_bp = Blueprint('auth', __name__)

google = None  # Will be set during app init


def init_google_oauth(app_oauth):
    global google
    google = app_oauth.google


@auth_bp.route('/set_language/<lang>', endpoint='set_language_route')
def set_language_route(lang):
    if lang not in ['en', 'ar']:
        lang = 'ar'
    resp = make_response(redirect(request.referrer or url_for('home')))
    resp.set_cookie('lang', lang)
    return resp


@auth_bp.route('/create-translation', methods=['GET', 'POST'], endpoint='create_a_translation_item')
def create_a_translation_item():
    if request.method == 'POST':
        key = request.form.get('key')
        value_en = request.form.get('value_en')
        value_ar = request.form.get('value_ar')
        existing_translation = Translation.query.filter_by(key=key).first()
        if existing_translation:
            existing_translation.value_en = value_en
            existing_translation.value_ar = value_ar
        else:
            new_translation = Translation(
                key=key,
                value_en=value_en,
                value_ar=value_ar
            )
            db.session.add(new_translation)
        try:
            db.session.commit()
            flash(f"{g.translations['Translation_for']} \"{key}\" {g.translations['committed_successfully']}.", 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash(f"{g.translations['Failed_to_commit_translation_for']} \"{key}\": {e}.", 'danger')
    return render_template('create_translation.html')


@auth_bp.route('/google/login', endpoint='google_login')
def google_login():
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)


@auth_bp.route('/google/callback', endpoint='google_callback')
def google_callback():
    google.authorize_access_token()
    user_info = google.get('userinfo').json()
    email = user_info['email']
    full_name = user_info.get('name', 'not available')

    user = User.query.filter_by(username=email).first()
    if user:
        if user.role == 'admin' and user.totp_secret:
            session['pending_2fa_user_id'] = user.id
            return redirect(url_for('verify_2fa'))
        elif user.role == 'admin' and not user.totp_secret:
            login_user(user, remember=True, duration=timedelta(days=30))
            return redirect(url_for('setup_2fa'))
        login_user(user, remember=True, duration=timedelta(days=30))
        return redirect(url_for('home'))
    else:
        new_user = User(
            username=email,
            role="client",
            confirmed=True,
            full_name=full_name,
            mobile="not available",
            address="not available",
            area="not available"
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user, remember=True, duration=timedelta(days=30))
        return redirect(url_for('complete_profile'))


@auth_bp.route('/complete-profile', methods=["GET", "POST"], endpoint='complete_profile')
@login_required
def complete_profile():
    if request.method == "POST":
        full_name = request.form.get("full_name", current_user.full_name)
        mobile = request.form.get("mobile")
        address = request.form.get("address")
        area = request.form.get("area")
        current_user.full_name = full_name
        current_user.mobile = mobile
        current_user.address = address
        current_user.area = area
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("complete_profile.html", governorates=EGYPT_GOVERNORATES)


@auth_bp.route("/login", methods=["GET", "POST"], endpoint='login')
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user and user.locked_until and user.locked_until > datetime.now(ZoneInfo("UTC")):
            remaining = (user.locked_until - datetime.now(ZoneInfo("UTC"))).seconds // 60 + 1
            flash(g.translations.get("account_locked", "Account locked. Try again in {remaining} minutes.").format(remaining=remaining), "danger")
            time.sleep(1)
            return render_template("login.html")

        if user and user.password and check_password_hash(user.password, password) and user.confirmed:
            user.failed_login_attempts = 0
            user.locked_until = None
            db.session.commit()

            if user.role == 'admin':
                if user.totp_secret:
                    session['pending_2fa_user_id'] = user.id
                    return redirect(url_for('verify_2fa'))
                else:
                    login_user(user, remember=True, duration=timedelta(days=30))
                    return redirect(url_for('setup_2fa'))

            login_user(user, remember=True, duration=timedelta(days=30))
            return redirect(url_for("home"))
        elif user and user.password and check_password_hash(user.password, password) and not user.confirmed:
            flash(g.translations["your_email_hasnt_confirmed"], "danger")
            time.sleep(1)
        elif user and user.confirmed and not user.password:
            flash(g.translations["use_google_sign_in_please"], "danger")
            time.sleep(1)
        else:
            if user:
                user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                if user.failed_login_attempts >= 7:
                    user.locked_until = datetime.now(ZoneInfo("UTC")) + timedelta(minutes=15)
                    flash(g.translations.get("account_locked_after_attempts", "Too many failed attempts. Account locked for 15 minutes."), "danger")
                else:
                    flash(g.translations["login_unsuccessful_please_check_username_and_password"], "danger")
                db.session.commit()
            else:
                flash(g.translations["login_unsuccessful_please_check_username_and_password"], "danger")
            time.sleep(1)
    return render_template("login.html")


@auth_bp.route('/reset_password_request', methods=['GET', 'POST'], endpoint='reset_password_request')
def reset_password_request():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(username=email).first()
        if user:
            token = generate_reset_token(user)
            send_password_reset_email(user, token)
            flash(g.translations["an_email_has_been_sent_with_instructions_to_reset_your_password"], "success")
            return redirect(url_for('login'))
        else:
            flash(g.translations["email_address_is_not_valid"], "danger")
    return render_template('reset_password_request.html')


@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'], endpoint='reset_password')
def reset_password(token):
    user = verify_reset_token(token)
    if not user:
        flash(g.translations["that_is_an_invalid_or_expired_link"], "danger")
        return redirect(url_for('reset_password_request'))
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        valid, msg = validate_password(password)
        if not valid:
            flash(msg, "danger")
            return redirect(url_for('reset_password', token=token))
        if password != confirm_password:
            flash(g.translations["passwords_do_not_match"], "danger")
            return redirect(url_for('reset_password', token=token))
        user.password = generate_password_hash(password, method='scrypt')
        user.reset_token = None
        user.reset_token_expiration = None
        db.session.commit()
        flash(g.translations["your_password_has_been_updated_you_can_now_log_in"], "success")
        return redirect(url_for('login'))
    return render_template('reset_password.html', token=token)


@auth_bp.route("/signup", methods=["GET", "POST"], endpoint='signup')
@limiter.limit("20 per hour")
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        full_name = request.form["full_name"]
        mobile = request.form["mobile"]
        address = request.form["address"]
        area = request.form["area"]

        valid, msg = validate_username(username)
        if not valid:
            flash(msg, "danger")
            return redirect(url_for("signup", governorates=EGYPT_GOVERNORATES))

        valid, msg = validate_password(password)
        if not valid:
            flash(msg, "danger")
            return redirect(url_for("signup", governorates=EGYPT_GOVERNORATES))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            if existing_user.confirmed:
                flash(g.translations["username_already_exists_please_choose_a_different_one"], "danger")
                return redirect(url_for("signup", governorates=EGYPT_GOVERNORATES))
            else:
                existing_user.password = generate_password_hash(password, method='scrypt')
                existing_user.full_name = full_name
                existing_user.mobile = mobile
                existing_user.address = address
                existing_user.confirmed = False
                db.session.commit()
                token = ext.serializer.dumps(username, salt='email-confirm')
                confirm_url = url_for('confirm_email', token=token, _external=True)
                send_email_confirmation(username, confirm_url)
                flash(g.translations["a_confirmation_email_has_been_sent_please_check_your_email"], "success")
                return redirect(url_for("login"))

        hashed_password = generate_password_hash(password, method='scrypt')
        new_user = User(
            username=username,
            password=hashed_password,
            role="client",
            confirmed=False,
            full_name=full_name,
            mobile=mobile,
            address=address,
            area=area
        )
        db.session.add(new_user)
        db.session.commit()
        token = ext.serializer.dumps(username, salt='email-confirm')
        confirm_url = url_for('confirm_email', token=token, _external=True)
        send_email_confirmation(username, confirm_url)
        flash(g.translations["a_confirmation_email_has_been_sent_please_check_your_email"], "success")
        return redirect(url_for("login"))
    return render_template("signup.html", governorates=EGYPT_GOVERNORATES)


@auth_bp.route('/confirm/<token>', endpoint='confirm_email')
def confirm_email(token):
    try:
        email = ext.serializer.loads(token, salt='email-confirm', max_age=86400)
    except:
        email = None
        try:
            email = ext.serializer.loads(token, salt='email-confirm')
        except:
            flash(g.translations["the_confirmation_link_is_invalid_or_has_expired"], "danger")
            return redirect(url_for("signup"))

        user = User.query.filter_by(username=email).first()
        if user and not user.confirmed:
            new_token = ext.serializer.dumps(email, salt='email-confirm')
            confirm_url = url_for('confirm_email', token=new_token, _external=True)
            send_email_confirmation(email, confirm_url)
            flash(g.translations["your_confirmation_link_expired_a_new_one_has_been_sent"], "danger")
            return redirect(url_for("login"))
        else:
            flash(g.translations["the_confirmation_link_is_invalid_or_has_expired"], "danger")
            return redirect(url_for("signup"))

    user = User.query.filter_by(username=email).first()
    if user.confirmed:
        flash(g.translations["your_account_is_already_confirmed_please_log_in"], "success")
        return redirect(url_for("login"))
    user.confirmed = True
    db.session.commit()
    flash(g.translations["your_account_has_been_confirmed_please_log_in"], "success")
    return redirect(url_for("login"))


@auth_bp.route("/logout", endpoint='logout')
@login_required
def logout():
    save_cart_to_db()
    logout_user()
    return redirect(url_for("home"))


@auth_bp.route('/setup_2fa', methods=['GET', 'POST'], endpoint='setup_2fa')
@login_required
def setup_2fa():
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    if current_user.totp_secret:
        return redirect(url_for('home'))

    if request.method == 'POST':
        user_code = request.form.get('code')
        secret = session.get('setup_totp_secret')
        if not secret:
            flash(g.translations.get('2fa_setup_expired', 'Session expired. Please try setting up 2FA again.'), 'danger')
            return redirect(url_for('setup_2fa'))
        totp = pyotp.TOTP(secret)
        if totp.verify(user_code):
            current_user.totp_secret = secret
            db.session.commit()
            session.pop('setup_totp_secret', None)
            flash(g.translations.get('2fa_setup_success', '2FA Setup Successful!'), 'success')
            return redirect(url_for('home'))
        else:
            flash(g.translations.get('invalid_code', 'Invalid code. Please try again.'), 'danger')

    secret = pyotp.random_base32()
    session['setup_totp_secret'] = secret
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=current_user.username, issuer_name="Hawary Shop")
    # Force the use of the Pillow image factory
    img = qrcode.make(totp_uri, image_factory=PilImage)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_code_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return render_template('setup_2fa.html', secret=secret, qr_code_b64=qr_code_b64)


@auth_bp.route('/verify_2fa', methods=['GET', 'POST'], endpoint='verify_2fa')
def verify_2fa():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    pending_user_id = session.get('pending_2fa_user_id')
    if not pending_user_id:
        return redirect(url_for('login'))
    user = User.query.get(pending_user_id)
    if not user or not user.totp_secret:
        session.pop('pending_2fa_user_id', None)
        return redirect(url_for('login'))
    if request.method == 'POST':
        user_code = request.form.get('code')
        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(user_code):
            login_user(user, remember=True, duration=timedelta(days=30))
            session.pop('pending_2fa_user_id', None)
            flash(g.translations.get('login_successful', 'Login Successful!'), 'success')
            return redirect(url_for('home'))
        else:
            flash(g.translations.get('invalid_code', 'Invalid code. Please try again.'), 'danger')
    return render_template('verify_2fa.html')


@auth_bp.route('/googlec0366ebe098eff87.html', endpoint='google_verification')
def google_verification():
    return send_from_directory('static', 'googlec0366ebe098eff87.html')
