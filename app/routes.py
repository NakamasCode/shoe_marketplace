from flask import render_template, url_for, redirect, flash, request, session
from app import  app,db
from app.forms import ForgotPasswordForm,BuyerProfileForm,ResetPasswordForm,LoginForm, RegisterForm, SellerProfileForm, ProductForm, CategoryForm, DeleteForm, MessageForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, SellerProfile,BuyerProfile,SellerImage, Category, Product, ProductImage,SellerImage, Message
import os

from sqlalchemy import func
from urllib.parse import urlparse
from datetime import datetime, timedelta
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
    category_form = CategoryForm()
    category_form.parent_id.choices = [(0, 'No parent')] + [(c.id, c.name) for c in categories]
    form = CategoryForm()
    
    form.parent_id.choices = [(0, 'No parent')] + [(c.id, c.name) for c in categories]
    
    return render_template('seller_dashboard.html', title='Dashboard', products=products, category_form=category_form,categories=categories, form=form)


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
@app.route('/seller/profile', defaults={'user_id': None}, methods=['GET', 'POST'])
@app.route('/seller/profile/<int:user_id>', methods=['GET'])
@login_required
def seller_profile(user_id):
    # If no user_id, assume current user (for editing)
    if user_id is None:
        if current_user.role != 'seller':
            flash('Access Denied!', 'danger')
            return redirect(url_for('index'))
        profile_user = current_user
        editable = True
    else:
        profile_user = User.query.get_or_404(user_id)
        editable = False  # Buyers or other users cannot edit

    if profile_user.role != 'seller':
        flash('Access Denied!', 'danger')
        return redirect(url_for('index'))

    profile = profile_user.seller_profile

    if editable:
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
            # handle logo and gallery upload...
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('seller_profile'))

        gallery_images = profile.images.all() if profile else []
        gallery_fields = [form.gallery_image1, form.gallery_image2, form.gallery_image3, form.gallery_image4]

        return render_template('seller_profile.html',
                               profile=profile,
                               form=form,
                               gallery_fields=gallery_fields,
                               gallery_images=gallery_images,
                               editable=True)

    else:
        # Read-only view for buyers
        return render_template('seller_profile.html',
                               profile=profile,
                               editable=False)



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

@app.route('/seller/category/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    category = Category.query.get_or_404(id)

    if category.seller_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for('seller_dashboard'))

    form = CategoryForm(obj=category)

    form.parent_id.choices = [
        (0, "None")
    ] + [(c.id, c.name) for c in Category.query.filter_by(seller_id=current_user.id)]

    if form.validate_on_submit():
        category.name = form.name.data
        category.parent_id = form.parent_id.data or None
        db.session.commit()
        flash("Category updated!", "success")
        return redirect(url_for('seller_dashboard'))

    return render_template('edit_category.html', form=form)



@app.route('/seller/category/<int:id>/delete', methods=['POST'])
@login_required
def delete_category(id):
    category = Category.query.get_or_404(id)

    if category.seller_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for('seller_dashboard'))

    # Get or create "Uncategorized"
    uncategorized = Category.query.filter_by(
        seller_id=current_user.id,
        name="Uncategorized"
    ).first()

    if not uncategorized:
        uncategorized = Category(
            name="Uncategorized",
            seller_id=current_user.id
        )
        db.session.add(uncategorized)
        db.session.commit()

    # Move products to Uncategorized
    for product in category.products:
        product.category_id = uncategorized.id

    db.session.delete(category)
    db.session.commit()

    flash("Category deleted. Products moved to Uncategorized.", "success")
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
    # Get sellers who have products in stock along with their profile (if exists)
    sellers = (
        db.session.query(User, SellerProfile)
        .join(Product, Product.seller_id == User.id)
        .outerjoin(SellerProfile, SellerProfile.user_id == User.id)
        .filter(User.role == "seller")
        .filter(Product.stock_quantity > 0)
        .distinct(User.id)  # avoid duplicates if multiple products
        .all()
    )
    return render_template('buyers_sellers.html', sellers=sellers)

@app.route('/buyer/profile', methods=['GET', 'POST'])
@login_required
def buyer_profile():
    if current_user.role != 'buyer':
        flash("Access denied!", "danger")
        return redirect(url_for('index'))

    # Get or create the profile
    profile = BuyerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        profile = BuyerProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()

    form = BuyerProfileForm(obj=profile)

    # Pre-fill form (optional, already handled by WTForms obj=profile)
    if request.method == 'GET' and profile:
        form.full_name.data = profile.full_name
        form.email.data = profile.email
        form.billing_address.data = profile.billing_address
        form.payment_method.data = profile.payment_method

    if form.validate_on_submit():
        profile.full_name = form.full_name.data
        profile.email = form.email.data
        profile.billing_address = form.billing_address.data
        profile.payment_method = form.payment_method.data

        # Handle profile image upload
        if form.profile_image.data:
            file = form.profile_image.data
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.root_path, 'static/uploads', filename)
            file.save(filepath)
            profile.profile_image = filename

        profile.user.last_seen = datetime.utcnow()
        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('buyer_profile'))

    return render_template('buyer_profile.html', form=form, profile=profile)

    
    
@app.route('/cart')
@login_required
def view_cart():
    # Demo page for now
    return "<h1>Cart Page (Demo)</h1>"


@app.route('/payment-method')
@login_required
def payment_method():
    return "<h1>Payment Method Page (Demo)</h1>"

    
@app.route('/buyers/seller/<int:seller_id>/products')
def view_seller_products(seller_id):
    seller = User.query.get_or_404(seller_id)
    products = Product.query.filter_by(seller_id=seller_id).all()
    categories = Category.query.filter_by(seller_id=seller_id).all()
    return render_template('buyers_product.html', seller=seller, products=products, categories= categories)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    seller = User.query.get(product.seller_id)
    images = product.images.all()

    is_seller_view = (
        current_user.is_authenticated and 
        current_user.id == product.seller_id
    )

    return render_template(
        'product_detail.html',
        product=product,
        seller=seller,
        images=images,
        is_seller_view=is_seller_view
    )


@app.route('/product/<int:product_id>/message', methods=['GET', 'POST'])
@login_required
def message_seller(product_id):
    product = Product.query.get_or_404(product_id)

    # Only buyers can send messages
    if current_user.role != 'buyer':
        flash("Only buyers can send messages to sellers.", "danger")
        return redirect(url_for('product_detail', product_id=product.id))

    seller = User.query.get_or_404(product.seller_id)
    form = MessageForm()

    if form.validate_on_submit():
        # Create and save the message
        msg = Message(
            sender_id=current_user.id,
            receiver_id=seller.id,
            product_id=product.id,
            content=form.content.data
        )
        db.session.add(msg)
        db.session.commit()
        flash("Message sent to seller!", "success")
        return redirect(url_for('product_detail', product_id=product.id))

    return render_template('message_form.html', form=form, product=product, seller=seller)

@app.route('/inbox')
@login_required
def inbox():
    products_info = []

    if current_user.role == 'seller':
        # Seller view
        products = Product.query.filter_by(seller_id=current_user.id).all()
        for product in products:
            messages = Message.query.filter_by(product_id=product.id).order_by(Message.timestamp.desc()).all()
            buyers_dict = {}
            for msg in messages:
                if not msg.product or msg.sender_id == current_user.id:
                    continue
                buyer_id = msg.sender_id
                if buyer_id not in buyers_dict:
                    buyers_dict[buyer_id] = {
                        "id": buyer_id,
                        "username": msg.sender.username,
                        "message_count": 0
                    }
                buyers_dict[buyer_id]["message_count"] += 1

            buyers = list(buyers_dict.values())
            new_messages_count = Message.query.filter(
                Message.product_id == product.id,
                Message.sender_id != current_user.id,
                Message.timestamp > datetime.utcnow() - timedelta(days=1)
            ).count()

            products_info.append({
                "product": product,
                "buyers": buyers,
                "new_messages_count": new_messages_count
            })

    else:
        # Buyer view
        # Get products buyer has messaged
        messages = Message.query.filter(
            (Message.sender_id == current_user.id) |
            (Message.receiver_id == current_user.id)  # assuming you track receiver_id
        ).order_by(Message.timestamp.desc()).all()

        products_dict = {}
        for msg in messages:
            if not msg.product:
                continue
            pid = msg.product.id
            if pid not in products_dict:
                products_dict[pid] = {
                    "product": msg.product,
                    "last_message": msg.content,
                    "timestamp": msg.timestamp
                }
        # convert to list
        products_info = list(products_dict.values())

    return render_template('inbox.html', products_info=products_info)


@app.route('/messages/<int:product_id>/<int:user_id>', methods=['GET', 'POST'])
@login_required
def conversation(product_id, user_id):
    product = Product.query.get_or_404(product_id)
    other_user = User.query.get_or_404(user_id)

    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(
            sender_id=current_user.id,
            receiver_id=other_user.id,
            product_id=product.id,
            content=form.content.data
        )
        db.session.add(msg)
        db.session.commit()
        return redirect(url_for('conversation', product_id=product.id, user_id=other_user.id))

    # Fetch conversation messages
    msgs = Message.query.filter(
        ((Message.sender_id==current_user.id) & (Message.receiver_id==other_user.id)) |
        ((Message.sender_id==other_user.id) & (Message.receiver_id==current_user.id))
    ).filter_by(product_id=product.id).order_by(Message.timestamp).all()

    return render_template('conversation.html', messages=msgs, form=form, product=product, other_user=other_user)



@app.route('/forgot-password')
def forgot_password():
    form = ForgotPasswordForm()
    return render_template('forgot_password.html', title='Forgot Password', form=form)

# -------------------------
# RESET PASSWORD PAGE
# -------------------------
@app.route('/reset-password')
def reset_password():
    form = ResetPasswordForm()
    return render_template('reset_password.html', title='Reset Password', form=form)