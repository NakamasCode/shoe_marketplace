from flask import render_template, url_for, redirect, flash, request
from app import app, db
from app.forms import LoginForm, RegisterForm, SellerProfileForm, ProductForm, CategoryForm, DeleteForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, SellerProfile,SellerImage, Category, Product, ProductImage,SellerImage
import os
from urllib.parse import urlparse
from datetime import datetime
from werkzeug.utils import secure_filename


# ------------------------- PUBLIC ROUTES -------------------------

@app.route('/')
@app.route('/index')
def index():
    if current_user.is_authenticated:
        # Redirect logged-in users directly to their dashboard
        if current_user.role == 'seller':
            return redirect(url_for('seller_dashboard'))
        else:
            return redirect(url_for('select_seller'))
    
    # Public homepage for not-logged-in users
    return render_template('index.html', title='Home')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember.data)

        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            return redirect(url_for('seller_dashboard') if user.role == 'seller' else url_for('select_seller'))

        return redirect(next_page)

    return render_template('login.html', title='Sign In', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registered successfully!', 'success')
        login_user(user)

        # Create SellerProfile if role is seller
        if user.role == 'seller':
            profile = SellerProfile(user_id=user.id)
            db.session.add(profile)
            db.session.commit()
            return redirect(url_for('seller_dashboard'))
        return redirect(url_for('select_seller'))

    return render_template('register.html', title='Register', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


# ------------------------- DASHBOARDS -------------------------

@app.route('/seller/dashboard')
@login_required
def seller_dashboard():
    if current_user.role != 'seller':
        flash("Access denied.", "danger")
        return redirect(url_for('index'))
    # Fetch seller's products and categories for dashboard
    products = Product.query.filter_by(seller_id=current_user.id).all()
    categories = Category.query.filter_by(seller_id=current_user.id).all()
    form = CategoryForm()
    
    form.parent_id.choices = [(0, 'No parent')] + [(c.id, c.name) for c in categories]
    
    return render_template('seller_dashboard.html', title='Dashboard', products=products, categories=categories, form=form)


# @app.route('/buyer/dashboard')
# @login_required
# def buyer_dashboard():
#     if current_user.role != 'buyer':
#         flash('Access Denied.', 'danger')
#         return redirect(url_for('index'))
#     # Show all sellers for buyer
#     sellers = User.query.filter_by(role='seller').all()
#     return render_template('buyer_dashboard.html', title='Dashboard', sellers=sellers)



@app.route('/seller/<int:id>')
@login_required
def view_seller(id):
    if current_user.role != 'buyer':
        flash("Access Denied.", "danger")
        return redirect(url_for('index'))

    seller = SellerProfile.query.get_or_404(id)
    
    # Fetch seller's products grouped by category
    categories = Category.query.filter_by(seller_id=seller.user_id).all()
    products = Product.query.filter_by(seller_id=seller.user_id).all()
    
    # Optional: group products by category
    products_by_category = {}
    for category in categories:
        products_by_category[category.name] = [p for p in products if p.category_id == category.id]
    
    # Products without category
    uncategorized = [p for p in products if not p.category_id]
    
    return render_template('view_seller.html',
                           seller=seller,
                           categories=categories,
                           products_by_category=products_by_category,
                           uncategorized=uncategorized)


# ------------------------- SELLER PROFILE -------------------------

@app.route('/seller/profile', methods=['GET', 'POST'])
@login_required
def seller_profile():
    if current_user.role != 'seller':
        flash('Access Denied!', 'danger')
        return redirect(url_for('index'))

    profile = current_user.seller_profile
    form = SellerProfileForm()

    # Pre-fill form
    if request.method == 'GET' and profile:
        form.shop_name.data = profile.shop_name
        form.about.data = profile.about
        form.phone_number.data = profile.phone_number
        form.location.data = profile.location
        form.open_hours.data = profile.open_hours

    if form.validate_on_submit():
        profile.shop_name = form.shop_name.data
        profile.about = form.about.data
        profile.phone_number = form.phone_number.data
        profile.location = form.location.data
        profile.open_hours = form.open_hours.data

        # Update logo
        if form.shop_logo.data:
            file = form.shop_logo.data
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.root_path, 'static/uploads', filename)
            file.save(filepath)
            profile.shop_logo = filename

        # Add gallery images
        for field in [form.gallery_image1, form.gallery_image2, form.gallery_image3, form.gallery_image4]:
            if field.data:
                file = field.data
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.root_path, 'static/uploads', filename)
                file.save(filepath)
                gallery_image = SellerImage(seller_profile_id=profile.id, image_url=filename)
                db.session.add(gallery_image)

        profile.user.last_seen = datetime.utcnow()
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('seller_profile'))

    # Fetch existing gallery images
    gallery_images = profile.images.all() if profile else []

    # Prepare gallery fields for template loop
    gallery_fields = [form.gallery_image1, form.gallery_image2, form.gallery_image3, form.gallery_image4]

    return render_template('seller_profile.html',
                           title='Seller Profile',
                           form=form,
                           gallery_fields=gallery_fields,
                           gallery_images=gallery_images,
                           profile=profile)



@app.route("/seller/<int:seller_id>/delete_logo", methods=["POST"])
@login_required
def delete_logo(seller_id):
    profile = SellerProfile.query.get_or_404(seller_id)

    # ownership check
    if profile.user_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("seller_profile"))

    if profile.shop_logo:
        logo_path = os.path.join(app.root_path, "static", "uploads", profile.shop_logo)
        if os.path.exists(logo_path):
            try:
                os.remove(logo_path)
            except OSError:
                pass

        profile.shop_logo = None
        db.session.commit()
        flash("Logo deleted.", "success")
    else:
        flash("No logo to delete.", "info")

    return redirect(url_for("seller_profile"))



@app.route("/seller/gallery/<int:image_id>/delete", methods=["POST"])
@login_required
def delete_gallery_image(image_id):
    img = SellerImage.query.get_or_404(image_id)

    # ownership check: ensure current user owns this seller profile
    if img.seller_profile.user_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("seller_profile"))

    img_path = os.path.join(app.root_path, "static", "uploads", img.image_url)
    if os.path.exists(img_path):
        try:
            os.remove(img_path)
        except OSError:
            pass

    db.session.delete(img)
    db.session.commit()
    flash("Gallery image deleted.", "success")
    return redirect(url_for("seller_profile"))


# ------------------------- CATEGORY ROUTES -------------------------

@app.route('/seller/category/add', methods=['POST'])
@login_required
def quick_add_category():
    if current_user.role != 'seller':
        flash("Access denied.", "danger")
        return redirect(url_for('seller_dashboard'))

    form = CategoryForm()
    categories = Category.query.filter_by(seller_id=current_user.id).all()
    form.parent_id.choices = [(0, 'No parent')] + [(c.id, c.name) for c in categories]

    if form.validate_on_submit():
        parent_id = form.parent_id.data if form.parent_id.data != 0 else None
        new_category = Category(
            name=form.name.data,
            parent_id=parent_id,
            seller_id=current_user.id
        )
        db.session.add(new_category)
        db.session.commit()
        flash(f'Category "{new_category.name}" added!', 'success')
        

    return redirect(url_for('seller_dashboard'))

@app.route('/seller/category/<int:id>/delete', methods=['POST'])
@login_required
def delete_category(id):
    category = Category.query.get_or_404(id)

    if category.seller_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for('seller_dashboard'))

    db.session.delete(category)
    db.session.commit()
    flash("Category deleted!", "success")
    return redirect(url_for('seller_dashboard'))


@app.route('/seller/product/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if current_user.role != 'seller':
        flash("Access denied.", "danger")
        return redirect(url_for('index'))

    form = ProductForm()

    # Load categories for this seller
    categories = Category.query.filter_by(seller_id=current_user.id).all()

    # If no categories exist, create a default one
    if not categories:
        default_category = Category(name="Uncategorized", seller_id=current_user.id)
        db.session.add(default_category)
        db.session.commit()
        categories = [default_category]

    # Populate the dropdown choices
    form.category_id.choices = [(c.id, c.name) for c in categories]

    product_image_fields = [
        form.product_image1,
        form.product_image2,
        form.product_image3,
        form.product_image4
    ]

    if form.validate_on_submit():
        selected_category = form.category_id.data if form.category_id.data != 0 else None

        # Create product
        new_product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            size_unit=form.size_unit.data,
            stock_quantity=form.stock_quantity.data,
            seller_id=current_user.id,
            category_id=selected_category
        )

        db.session.add(new_product)
        db.session.commit()

        # Handle image uploads
        for field in product_image_fields:
            file = field.data
            if file and file.filename:
                filename = secure_filename(file.filename)
                upload_path = os.path.join(app.root_path, 'static/uploads', filename)
                file.save(upload_path)

                product_image = ProductImage(
                    product_id=new_product.id,
                    image_url=filename
                )
                db.session.add(product_image)

        db.session.commit()

        flash(f'Product "{new_product.name}" added successfully!', 'success')
        return redirect(url_for('seller_dashboard'))

    return render_template(
        'add_product.html',
        title='Add Product',
        form=form,
        product_image_fields=product_image_fields
    )


@app.route('/seller/product/<int:product_id>')
@login_required
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)

    if product.seller_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for('seller_dashboard'))

    return render_template('product_detail.html', product=product)


@app.route('/seller/product/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)

    if product.seller_id != current_user.id:
        flash('Access Denied.', 'danger')
        return redirect(url_for('seller_dashboard'))

    form = ProductForm()

    # Load seller categories
    categories = Category.query.filter_by(seller_id=current_user.id).all()
    if not categories:
        default_category = Category(name="Uncategorized", seller_id=current_user.id)
        db.session.add(default_category)
        db.session.commit()
        categories = [default_category]
    form.category_id.choices = [(c.id, c.name) for c in categories]

    # Prepare image fields for template
    product_image_fields = [form.product_image1, form.product_image2, form.product_image3, form.product_image4]

    # Pre-fill form on GET
    if request.method == 'GET':
        form.name.data = product.name
        form.price.data = product.price
        form.description.data = product.description
        form.size_unit.data = product.size_unit
        form.stock_quantity.data = product.stock_quantity
        form.category_id.data = product.category_id if product.category_id else 0

    existing_images = product.images.order_by(ProductImage.id).all()  # ensures order

    if form.validate_on_submit():
        # Update basic fields
        product.name = form.name.data
        product.price = form.price.data
        product.description = form.description.data
        product.size_unit = form.size_unit.data
        product.stock_quantity = form.stock_quantity.data
        product.category_id = form.category_id.data if form.category_id.data != 0 else None

        # Handle image uploads (max 4)
        for idx, field in enumerate(product_image_fields):
            file = field.data
            if file and file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.root_path, 'static/uploads', filename)
                file.save(filepath)

                if idx < len(existing_images):
                    # Replace existing image
                    old_image = existing_images[idx]
                    old_path = os.path.join(app.root_path, 'static/uploads', old_image.image_url)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                    old_image.image_url = filename
                else:
                    # Add new image if less than 4 total
                    if len(existing_images) < 4:
                        new_img = ProductImage(product_id=product.id, image_url=filename)
                        db.session.add(new_img)

        db.session.commit()
        flash(f'Product "{product.name}" updated successfully!', 'success')
        return redirect(url_for('edit_product', id=product.id))

    return render_template(
        'edit_product.html',
        title=f"Edit Product - {product.name}",
        form=form,
        product=product,
        product_image_fields=product_image_fields,
        existing_images=existing_images
    )


@app.route('/seller/product/<int:id>/delete', methods=['POST'])
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    if product.seller_id != current_user.id:
        flash("Access Denied.", "danger")
        return redirect(url_for('seller_dashboard'))

    # Delete associated images first
    for img in product.images:
        filepath = os.path.join(app.root_path, 'static/uploads', img.image_url)
        if os.path.exists(filepath):
            os.remove(filepath)
        db.session.delete(img)

    db.session.delete(product)
    db.session.commit()
    flash('Product deleted!', 'success')
    return redirect(url_for('seller_dashboard'))


# ------------------------- PRODUCT IMAGE DELETE -------------------------

@app.route('/seller/product/image/<int:id>/delete', methods=['POST'])
@login_required
def delete_product_image(id):
    image = ProductImage.query.get_or_404(id)
    product = Product.query.get_or_404(image.product_id)

    if product.seller_id != current_user.id:
        flash("Access Denied.", "danger")
        return redirect(url_for('seller_dashboard'))

    filepath = os.path.join(app.root_path, 'static/uploads', image.image_url)
    if os.path.exists(filepath):
        os.remove(filepath)

    db.session.delete(image)
    db.session.commit()
    flash("Image deleted!", "success")
    return redirect(url_for('edit_product', id=product.id))


@app.route('/buyers/sellers')
@login_required
def select_seller():
    sellers = User.query.filter_by(role="seller").join(Product).filter(Product.stock_quantity > 0).all()
    return render_template('buyers_sellers.html', sellers=sellers)
    
    
    
@app.route('/buyers/seller/<int:seller_id>/products')
def view_seller_products(seller_id):
    seller = User.query.get_or_404(seller_id)
    products = Product.query.filter_by(seller_id=seller_id).all()
    categories = Category.query.filter_by(seller_id=seller_id).all()
    return render_template('buyers_product.html', seller=seller, products=products, categories= categories)