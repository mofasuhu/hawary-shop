"""Admin product CRUD: add, remove, update, manage sizes."""
import os, time
import cloudinary, cloudinary.uploader
from flask import Blueprint, render_template, redirect, url_for, flash, request, g
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.product import Product, ProductSize
from app.models.order import OrderItem
from app.utils.helpers import add_product_translations

admin_products_bp = Blueprint('admin_products', __name__)


@admin_products_bp.route("/add", methods=["GET", "POST"], endpoint='add')
@login_required
def add():
    if current_user.role != "admin": return redirect(url_for("home"))
    if request.method == "POST":
        name_en = request.form["name_en"]; name_ar = request.form["name_ar"]
        existing = Product.query.filter((Product.name_en.ilike(name_en)) | (Product.name_ar.ilike(name_ar))).first()
        if existing:
            flash(g.translations["this_product_name_already_exists"], "danger"); return redirect(url_for("add"))
        image_urls = []
        for i in range(1, 11):
            f = request.files.get(f'image_file_{i}'); u = request.form.get(f'image_url_{i}', '').strip(); final = ""
            if f and f.filename != '':
                fn = secure_filename(f.filename)
                ext = fn.rsplit('.', 1)[1].lower() if '.' in fn else ''
                if ext not in {'png','jpg','jpeg','webp'}:
                    flash(f"Invalid file type for image {i}.", "danger"); return redirect(url_for("add"))
                pid = f"products/{os.path.splitext(fn)[0]}_{int(time.time())}"
                r = cloudinary.uploader.upload(f, public_id=pid, transformation=[{'width':500,'height':500,'crop':'pad','background':'whitesmoke'},{'quality':'auto','fetch_format':'auto','dpr':'auto'}])
                final = r['secure_url']
            elif u: final = u
            image_urls.append(final)
        try:
            p = Product(name_en=name_en, name_ar=name_ar, category_en=request.form["category_en"].strip(), category_ar=request.form["category_ar"].strip(),
                ingredients_en=request.form["ingredients_en"].strip(), ingredients_ar=request.form["ingredients_ar"].strip(),
                gender_en=request.form["gender_en"].strip(), gender_ar=request.form["gender_ar"].strip(),
                description_en=request.form["description_en"].strip(), description_ar=request.form["description_ar"].strip(),
                discount_percent=float(request.form.get("discount_percent", 0) or 0),
                image_url=image_urls[0], image_url_2=image_urls[1], image_url_3=image_urls[2], image_url_4=image_urls[3],
                image_url_5=image_urls[4], image_url_6=image_urls[5], image_url_7=image_urls[6], image_url_8=image_urls[7],
                image_url_9=image_urls[8], image_url_10=image_urls[9])
            db.session.add(p); db.session.flush()
            for se, sa, pr, aq, wk, lc, wc, hc in zip(
                request.form.getlist("size_en[]"), request.form.getlist("size_ar[]"), request.form.getlist("price[]"),
                request.form.getlist("available_quantity[]"), request.form.getlist("weight_kg[]"),
                request.form.getlist("length_cm[]"), request.form.getlist("width_cm[]"), request.form.getlist("height_cm[]")):
                db.session.add(ProductSize(product_id=p.id, size_en=se.strip(), size_ar=sa.strip(), price=float(pr.strip()),
                    available_quantity=int(aq.strip()), weight_kg=float(wk.strip()), length_cm=float(lc.strip()),
                    width_cm=float(wc.strip()), height_cm=float(hc.strip())))
            add_product_translations(p); db.session.commit()
            flash(g.translations["New_Product_Added_Successfully"], "success"); return redirect(url_for("home"))
        except Exception as e:
            db.session.rollback(); flash(f"Error adding product: {e}", "danger"); return redirect(url_for("add"))
    return render_template("add.html")


@admin_products_bp.route("/remove", methods=["GET", "POST"], endpoint='remove')
@login_required
def remove():
    if current_user.role != "admin": return redirect(url_for("home"))
    products = Product.query.all()
    if request.method == "POST":
        pid = request.form.get("product_id")
        if pid:
            p = db.session.get(Product, int(pid))
            if p:
                if OrderItem.query.filter_by(product_id=pid).first():
                    flash(g.translations["cannot_remove_product_it_is_referenced_in_existing_orders"], "danger"); return redirect(url_for("remove"))
                db.session.delete(p); db.session.commit(); flash(g.translations["product_removed_successfully"], "success")
            else: flash(g.translations["product_not_found"], "danger")
            return redirect(url_for("home"))
    return render_template("remove.html", products=products)


@admin_products_bp.route("/update", methods=["GET", "POST"], endpoint='update')
@login_required
def update():
    if current_user.role != "admin": return redirect(url_for("home"))
    products = Product.query.order_by(Product.name_en).all(); selected = None
    if request.method == "POST":
        pid = request.form.get("product_id")
        if not pid: flash("Please select a product.", "warning"); return redirect(url_for("update"))
        product = db.session.get(Product, int(pid))
        if not product: flash("Product not found.", "danger"); return redirect(url_for("update"))
        if request.form.get("new_name_en") is not None:
            try:
                urls = []
                for i in range(1, 11):
                    f = request.files.get(f'image_file_{i}'); u = request.form.get(f'image_url_{i}', '').strip()
                    existing = getattr(product, f'image_url_{i}' if i > 1 else 'image_url', ''); final = existing
                    if f and f.filename != '':
                        fn = secure_filename(f.filename); ext = fn.rsplit('.', 1)[1].lower() if '.' in fn else ''
                        if ext not in {'png','jpg','jpeg','webp'}: flash(f"Invalid file type for image {i}.", "danger"); return redirect(url_for("update"))
                        r = cloudinary.uploader.upload(f, public_id=f"products/{os.path.splitext(fn)[0]}_{int(time.time())}", transformation=[{'width':500,'height':500,'crop':'pad','background':'whitesmoke'},{'quality':'auto','fetch_format':'auto','dpr':'auto'}])
                        final = r['secure_url']
                    elif u and u != '' and u != 'del': final = u
                    elif u == 'del': final = ''
                    urls.append(final)
                product.name_en = request.form["new_name_en"].strip() or product.name_en
                product.name_ar = request.form["new_name_ar"].strip() or product.name_ar
                product.category_en = request.form["new_category_en"].strip() or product.category_en
                product.category_ar = request.form["new_category_ar"].strip() or product.category_ar
                product.ingredients_en = request.form["new_ingredients_en"].strip()
                product.ingredients_ar = request.form["new_ingredients_ar"].strip()
                product.gender_en = request.form["new_gender_en"].strip()
                product.gender_ar = request.form["new_gender_ar"].strip()
                product.description_en = request.form["new_description_en"].strip() or product.description_en
                product.description_ar = request.form["new_description_ar"].strip() or product.description_ar
                product.discount_percent = float(request.form.get("new_discount_percent", 0) or 0)
                for idx, attr in enumerate(['image_url','image_url_2','image_url_3','image_url_4','image_url_5','image_url_6','image_url_7','image_url_8','image_url_9','image_url_10']):
                    setattr(product, attr, urls[idx])
                add_product_translations(product); db.session.commit()
                flash(g.translations["Product_Updated_Successfully"], "success"); return redirect(url_for("home"))
            except Exception as e:
                db.session.rollback(); flash(f"Error: {e}", "danger"); return redirect(url_for("update"))
        selected = product
    return render_template("update.html", products=products, selected_product=selected)


@admin_products_bp.route("/admin/products/manage_sizes/<int:product_id>", methods=["GET", "POST"], endpoint='admin_manage_product_sizes')
@login_required
def admin_manage_product_sizes(product_id):
    if current_user.role != "admin": return redirect(url_for("home"))
    product = Product.query.get_or_404(product_id)
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add_size":
            se=request.form.get("size_en","").strip(); sa=request.form.get("size_ar","").strip()
            ps=request.form.get("price","").strip(); aqs=request.form.get("available_quantity","").strip()
            wk=request.form.get("weight_kg","").strip(); lc=request.form.get("length_cm","").strip()
            wc=request.form.get("width_cm","").strip(); hc=request.form.get("height_cm","").strip()
            if not all([se,sa,ps,aqs,wk,lc,wc,hc]): flash(g.translations["all_fields_for_new_size_are_required"], "danger")
            else:
                try:
                    p=float(ps); aq=int(aqs); w=float(wk); l=float(lc); wi=float(wc); h=float(hc)
                    if p<=0: flash(g.translations["price_must_be_a_positive_number"], "danger")
                    elif aq<0: flash(g.translations["available_quantity_cannot_be_negative"], "danger")
                    elif any(v<0 for v in [w,l,wi,h]): flash(g.translations["dimensions_and_weight_cannot_be_negative"], "danger")
                    else:
                        db.session.add(ProductSize(product_id=product.id, size_en=se, size_ar=sa, price=p, available_quantity=aq, weight_kg=w, length_cm=l, width_cm=wi, height_cm=h))
                        db.session.commit(); add_product_translations(product); flash(g.translations["product_size_added_successfully"], "success")
                except ValueError: flash(g.translations["invalid_price_quantity_dimensions_or_weight_format"], "danger")
        elif action == "update_size":
            sid=request.form.get("size_id"); se=request.form.get("size_en","").strip(); sa=request.form.get("size_ar","").strip()
            ps=request.form.get("price","").strip(); aqs=request.form.get("available_quantity","").strip()
            wk=request.form.get("weight_kg","").strip(); lc=request.form.get("length_cm","").strip()
            wc=request.form.get("width_cm","").strip(); hc=request.form.get("height_cm","").strip()
            if not all([sid,se,sa,ps,aqs,wk,lc,wc,hc]): flash(g.translations["all_fields_for_updating_size_are_required"], "danger")
            else:
                s = db.session.get(ProductSize, int(sid))
                if s and s.product_id == product.id:
                    try:
                        p=float(ps); aq=int(aqs); w=float(wk); l=float(lc); wi=float(wc); h=float(hc)
                        if p<=0: flash(g.translations["price_must_be_a_positive_number"], "danger")
                        elif aq<0: flash(g.translations["available_quantity_cannot_be_negative"], "danger")
                        elif any(v<0 for v in [w,l,wi,h]): flash(g.translations["dimensions_and_weight_cannot_be_negative"], "danger")
                        else:
                            s.size_en=se; s.size_ar=sa; s.price=p; s.available_quantity=aq; s.weight_kg=w; s.length_cm=l; s.width_cm=wi; s.height_cm=h
                            db.session.commit(); add_product_translations(product); flash(g.translations["product_size_updated_successfully"], "success")
                    except ValueError: flash(g.translations["invalid_price_quantity_dimensions_or_weight_format"], "danger")
                else: flash(g.translations["product_size_not_found_or_does_not_belong_to_this_product"], "danger")
        elif action == "delete_size":
            sid = request.form.get("size_id")
            if not sid: flash(g.translations["no_size_id_provided_for_deletion"], "danger")
            else:
                s = db.session.get(ProductSize, int(sid))
                if s and s.product_id == product.id:
                    if OrderItem.query.filter_by(product_size_id=s.id).first(): flash(g.translations["cannot_delete_size_it_is_referenced_in_existing_orders"], "danger")
                    else: db.session.delete(s); db.session.commit(); flash(g.translations["product_size_deleted_successfully"], "success")
                else: flash(g.translations["product_size_not_found_or_does_not_belong_to_this_product"], "danger")
        return redirect(url_for("admin_manage_product_sizes", product_id=product.id))
    return render_template("manage_product_sizes.html", product=product)
