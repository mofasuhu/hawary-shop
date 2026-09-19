from functools import wraps
from flask import redirect, url_for, flash, g
from flask_login import current_user, login_required


def admin_required(f):
    """Decorator that requires admin or superadmin role."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != "admin" and not current_user.superadmin:
            flash(g.translations["unauthorized_access"], "danger")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated_function


def superadmin_required(f):
    """Decorator that requires superadmin role."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.superadmin:
            flash(g.translations["unauthorized_access"], "danger")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated_function
