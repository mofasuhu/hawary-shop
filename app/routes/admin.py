import os
import csv
import json
import time
import random
import string
from io import BytesIO, StringIO
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import psycopg2
import cloudinary
import cloudinary.uploader
from openpyxl import Workbook
from datetime import time as dttime
from flask import Blueprint, render_template, redirect, url_for, flash, request, g, jsonify, send_file, current_app
from flask_login import login_required, current_user
from flask_mail import Message
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from sqlalchemy import func, case, and_
from sqlalchemy.orm import aliased
from app.extensions import db, mail
from app.models.user import User, UserWishlist
from app.models.product import Product, ProductSize
from app.models.order import Order, OrderItem
from app.models.payment import Transaction, PromoCode
from app.models.delivery import GovernorateDeliveryFee
from app.config import EGYPT_GOVERNORATES
from app.utils.validators import validate_username, validate_password
from app.utils.helpers import (
    today, mydtfmt, end_date_correction, add_product_translations, get_unique_values
)
from app.utils.filters import datetimeformat, to_cairo_time
from app.services.delivery import calculate_delivery_fees
from app.services.payment import process_refund

cairo_tz = ZoneInfo("Africa/Cairo")
admin_bp = Blueprint('admin', __name__)


@admin_bp.route("/superadmin_admin_signup", methods=["GET", "POST"], endpoint='superadmin_admin_signup')
@login_required
def superadmin_admin_signup():
    if not current_user.superadmin:
        return redirect(url_for("home"))
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        full_name = request.form["full_name"]
        mobile = request.form["mobile"]
        address = request.form["address"]
        area = request.form["area"]
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash(g.translations["username_already_exists_please_choose_a_different_one"], "danger")
            return redirect(url_for("superadmin_admin_signup"))
        valid, msg = validate_username(username)
        if not valid:
            flash(msg, "danger")
            return redirect(url_for("superadmin_admin_signup"))
        valid, msg = validate_password(password)
        if not valid:
            flash(msg, "danger")
            return redirect(url_for("superadmin_admin_signup"))
        hashed_password = generate_password_hash(password, method='scrypt')
        new_user = User(username=username, password=hashed_password, role="admin",
                        confirmed=True, full_name=full_name, mobile=mobile, address=address, area=area)
        db.session.add(new_user)
        db.session.commit()
        flash(g.translations["admin_account_created_successfully"], "success")
        return redirect(url_for("admin_accounts_manager"))
    return render_template("superadmin_admin_signup.html", governorates=EGYPT_GOVERNORATES)


@admin_bp.route("/admin/wishlists", methods=["GET"], endpoint='admin_wishlists')
@login_required
def admin_wishlists():
    if current_user.role not in ['admin', 'superadmin']:
        flash(g.translations.get('unauthorized_access', 'Unauthorized Access'), 'danger')
        return redirect(url_for('home'))
    page = request.args.get('page', 1, type=int)
    wishlists_pagination = UserWishlist.query.join(User).order_by(UserWishlist.updated_at.desc()).paginate(page=page, per_page=50, error_out=False)
    return render_template("admin_wishlists.html", wishlists=wishlists_pagination.items, pagination=wishlists_pagination, Product=Product)


@admin_bp.route("/admin/accounts", methods=["GET"], endpoint='admin_accounts_manager')
@login_required
def admin_accounts_manager():
    if current_user.role not in ['admin', 'superadmin']:
        flash(g.translations['unauthorized_access'], 'danger')
        return redirect(url_for('home'))
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '', type=str)
    sort_by = request.args.get('sort_by', 'id', type=str)
    sort_order = request.args.get('sort_order', 'asc', type=str)
    filter_area = request.args.get('area', '', type=str)

    last_order_subquery = db.session.query(
        Order.user_id, func.max(Order.date).label('last_order_date')
    ).group_by(Order.user_id).subquery('last_order_subquery')

    order_agg_subquery = db.session.query(
        Order.user_id,
        func.count(case((Order.status == 'Delivered', Order.id))).label('completed_orders_count'),
        func.sum(case((Order.status == 'Delivered', Order.order_total_price), else_=0)).label('total_completed_orders')
    ).group_by(Order.user_id).subquery('order_agg_subquery')

    query = db.session.query(User)
    query = query.outerjoin(last_order_subquery, User.id == last_order_subquery.c.user_id)
    query = query.outerjoin(order_agg_subquery, User.id == order_agg_subquery.c.user_id)

    LastOrder = aliased(Order)
    query = query.outerjoin(LastOrder, and_(
        User.id == LastOrder.user_id,
        last_order_subquery.c.last_order_date == LastOrder.date
    ))

    if search_query:
        search_term = f"%{search_query.lower().strip()}%"
        query = query.filter(
            (func.lower(User.username).like(search_term)) |
            (func.lower(User.full_name).like(search_term)) |
            (func.lower(User.mobile).like(search_term)) |
            (func.lower(User.address).like(search_term))
        )
    if filter_area:
        query = query.filter(User.area == filter_area)

    sort_map = {
        'id': User.id, 'full_name': User.full_name, 'role': User.role,
        'area': User.area, 'activated': User.confirmed,
        'last_order_date': last_order_subquery.c.last_order_date,
        'last_order_status': LastOrder.status,
        'completed_orders_count': order_agg_subquery.c.completed_orders_count,
        'total_completed_orders': order_agg_subquery.c.total_completed_orders
    }
    if sort_by in sort_map:
        sort_column = sort_map[sort_by]
        if sort_order == 'desc':
            query = query.order_by(sort_column.desc().nullslast())
        else:
            query = query.order_by(sort_column.asc().nullsfirst())

    pagination = query.paginate(page=page, per_page=50, error_out=False)
    clients = pagination.items
    return render_template('admin_accounts_manager.html', clients=clients, pagination=pagination,
                           search_query=search_query, sort_by=sort_by, sort_order=sort_order,
                           filter_area=filter_area, governorates=EGYPT_GOVERNORATES)


@admin_bp.route("/download_accounts_data", endpoint='download_accounts_data')
@login_required
def download_accounts_data():
    if current_user.role != "admin":
        return redirect(url_for("home"))
    clients = User.query.order_by(User.role).all()
    clients_data = [
        {
            g.translations["ID"]: client.id,
            g.translations["Username"]: client.username,
            g.translations["activated"]: g.translations['activated'] if client.confirmed else g.translations['not_activated'],
            g.translations["Full_Name"]: client.full_name,
            g.translations["Role"]: g.translations['super_admin'] if client.superadmin else g.translations[client.role],
            g.translations["Mobile"]: client.mobile,
            g.translations["Delivering_Area"]: g.translations[client.area],
            g.translations["Address"]: client.address,
            g.translations["Payment_Methods"]: ' - '.join([g.translations[x.strip().replace(' ','_')] for x in client.payment_methods_used.split(',')]) if client.payment_methods_used else '—',
            g.translations["Current_Payment_Method"]: '—' if not client.last_payment_method else g.translations[client.last_payment_method.replace(' ','_')],
            g.translations["total_completed_orders"]: sum(float(order.order_total_price) for order in (client.orders or []) if order.status == 'Delivered'),
            g.translations["completed_orders_count"]: len([order for order in (client.orders or []) if order.status == 'Delivered']),
            g.translations["last_order_date"]: datetimeformat(to_cairo_time(max((order.date for order in (client.orders or [])), default=None))) or "—",
            g.translations["last_order_status"]: (g.translations[sorted(client.orders, key=lambda o: o.date)[-1].status] if client.orders else "—")
        }
        for client in clients
    ]
    df = pd.DataFrame(clients_data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Clients")
    output.seek(0)
    return send_file(output, download_name=f"{today()}-clients.xlsx", as_attachment=True)


@admin_bp.route("/admin/accounts/delete/<int:account_id>", methods=["POST"], endpoint='superadmin_delete_account')
@login_required
def superadmin_delete_account(account_id):
    if current_user.role != "admin":
        return redirect(url_for("home"))
    client = User.query.get_or_404(account_id)
    orders = Order.query.filter_by(user_id=account_id).all()
    for order in orders:
        OrderItem.query.filter_by(order_id=order.id).delete()
        Transaction.query.filter_by(order_id=order.id).delete()
        db.session.delete(order)
    db.session.delete(client)
    db.session.commit()
    flash(g.translations["client_and_related_orders_deleted_successfully"], "success")
    return redirect(url_for("admin_accounts_manager"))


@admin_bp.route("/admin/accounts/superadmin_delete_admin/<int:client_id>", methods=["POST"], endpoint='superadmin_delete_admin')
@login_required
def superadmin_delete_admin(client_id):
    if not current_user.superadmin:
        return redirect(url_for("home"))
    admin_account = User.query.get_or_404(client_id)
    if admin_account.superadmin:
        flash(g.translations["cannot_delete_the_super_admin_account"], "danger")
        return redirect(url_for("admin_accounts_manager"))
    db.session.delete(admin_account)
    db.session.commit()
    flash(g.translations["admin_deleted_successfully"], "success")
    return redirect(url_for("admin_accounts_manager"))


@admin_bp.route("/admin/accounts/edit/<int:account_id>", methods=["GET", "POST"], endpoint='superadmin_edit_account')
@login_required
def superadmin_edit_account(account_id):
    if current_user.role != "admin":
        return redirect(url_for("home"))
    client = User.query.get_or_404(account_id)
    if request.method == "POST":
        client.full_name = request.form["full_name"]
        client.mobile = request.form["mobile"]
        client.area = request.form["area"]
        client.address = request.form["address"]
        db.session.commit()
        flash(g.translations["account_details_updated_successfully"], "success")
        return redirect(url_for("admin_accounts_manager"))
    return render_template("superadmin_edit_account.html", client=client, governorates=EGYPT_GOVERNORATES)


@admin_bp.route("/admin/orders", methods=["GET"], endpoint='orders_admin_viewer')
@login_required
def orders_admin_viewer():
    if current_user.role not in ['admin', 'superadmin']:
        flash(g.translations['unauthorized_access'], 'danger')
        return redirect(url_for("home"))
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '', type=str)
    sort_by = request.args.get('sort_by', 'date', type=str)
    sort_order = request.args.get('sort_order', 'desc', type=str)
    filter_status = request.args.get('status', '', type=str)

    query = db.session.query(Order).join(User).outerjoin(Transaction)
    if search_query:
        search_term = f"%{search_query.lower().strip()}%"
        order_ids_with_matching_items = db.session.query(Order.id).join(OrderItem).join(Product).filter(
            (func.lower(Product.name_en).like(search_term)) | (func.lower(Product.name_ar).like(search_term))
        ).distinct()
        query = query.filter(
            (func.lower(User.username).like(search_term)) | (func.lower(User.full_name).like(search_term)) |
            (func.lower(User.mobile).like(search_term)) | (func.lower(Order.recipient_name).like(search_term)) |
            (func.lower(Order.recipient_phone).like(search_term)) | (func.lower(Order.address).like(search_term)) |
            (func.lower(Transaction.transaction_id).like(search_term)) | (Order.id.in_(order_ids_with_matching_items))
        )
    if filter_status:
        query = query.filter(Order.status == filter_status)

    sort_map = {'id': Order.id, 'date': Order.date, 'client_id': User.id, 'payment_method': Order.payment_method,
                'payment_status': Order.payment_status, 'status': Order.status, 'total_price': Order.order_total_price}
    if sort_by in sort_map:
        sort_column = sort_map[sort_by]
        if sort_order == 'desc':
            query = query.order_by(sort_column.desc().nullslast())
        else:
            query = query.order_by(sort_column.asc().nullsfirst())

    pagination = query.paginate(page=page, per_page=50, error_out=False)
    orders = pagination.items
    all_statuses = [status[0] for status in db.session.query(Order.status).distinct().all()]
    return render_template('orders_admin_viewer.html', orders=orders, pagination=pagination,
                           search_query=search_query, sort_by=sort_by, sort_order=sort_order,
                           filter_status=filter_status, all_statuses=all_statuses)


@admin_bp.route("/download_orders_data", endpoint='download_orders_data')
@login_required
def download_orders_data():
    if current_user.role != "admin":
        return redirect(url_for("home"))
    orders = Order.query.order_by(Order.date.desc()).all()
    orders_data = []
    for order in orders:
        order_total = 0
        for i, item in enumerate(order.items, 1):
            order_total += item.quantity * item.price
            product_name = item.product.name_ar if g.current_language == 'ar' else item.product.name_en
            product_size_name = ""
            if item.product_size:
                product_size_name = item.product_size.size_ar if g.current_language == 'ar' else item.product_size.size_en
            full_product_description = f"{product_name} ({product_size_name})" if product_size_name else product_name
            order_dict = {
                g.translations["Client_ID"]: order.user.id,
                g.translations["Username"]: order.user.username,
                g.translations["Full_Name"]: order.user.full_name,
                g.translations["Ordering_Date"]: datetimeformat(to_cairo_time(order.date)),
                g.translations["Mobile"]: order.user.mobile,
                g.translations["Address"]: order.user.address,
                g.translations["Pay_Method"]: g.translations[order.payment_method.replace(' ', '_')],
                g.translations["Pay_Status"]: g.translations[order.payment_status.replace(' ', '_')],
                g.translations["Status"]: g.translations[order.status],
                g.translations["Order_ID"]: order.id,
                g.translations["Item"]: full_product_description,
                f"{g.translations['Quantity']} ({g.translations['piece']})": item.quantity,
                f"{g.translations['Item_Price']} ({g.translations['EGP']})": item.price,
                f"{g.translations['Item_Total']} ({g.translations['EGP']})": item.quantity * item.price,
                f"{g.translations['Order_Total']} ({g.translations['EGP']})": order_total if i == len(order.items) else "",
                f"{g.translations['Delivery_Fees']} ({g.translations['EGP']})": order.delivery_fees if i == len(order.items) else "",
                f"{g.translations['Grand_Total']} ({g.translations['EGP']})": order.order_total_price if i == len(order.items) else "",
                g.translations['Promocode']: g.translations['No_Promocode'] if order.order_promocode_used == "No Promocode" and i == len(order.items) else (order.order_promocode_used if i == len(order.items) else ""),
                f"{g.translations['Discount']} (%)": order.order_discount_percent if i == len(order.items) else "",
                g.translations["PayMob_Parent_Transaction_ID"]: order.transaction.transaction_id if order.transaction and i == len(order.items) else (g.translations["No_Trn"] if i == len(order.items) else ""),
                f"{g.translations['Transaction_Net_Amount']} ({g.translations['EGP']})": (order.transaction.net_amount_cents / 100) if order.transaction and i == len(order.items) else (g.translations["No_Trn"] if i == len(order.items) else ""),
                f"{g.translations['Refunded_Amount']} ({g.translations['EGP']})": (order.transaction.refunded_amount_cents / 100) if order.transaction and i == len(order.items) else (g.translations["No_Trn"] if i == len(order.items) else ""),
            }
            orders_data.append(order_dict)
    df = pd.DataFrame(orders_data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Orders")
    output.seek(0)
    return send_file(output, download_name=f"{today()}-orders.xlsx", as_attachment=True)
