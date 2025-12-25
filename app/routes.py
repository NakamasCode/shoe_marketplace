from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.datastructures import FileStorage

import uuid

from app import db
from app.forms import (
    ForgotPasswordForm, BuyerProfileForm, ResetPasswordForm,
    LoginForm, RegisterForm, SellerProfileForm, ProductForm,
    CategoryForm, MessageForm
)
from app.models import (
    User, SellerProfile, BuyerProfile, SellerImage,
    Category, Product, ProductImage, Message
)
from urllib.parse import urlparse
from datetime import datetime, timedelta
import cloudinary.uploader

main = Blueprint("main", __name__)

# =========================
# CLOUDINARY HELPERS
# =========================
from cloudinary.exceptions import NotFound

def upload_to_cloudinary(file, folder, public_id):
    if isinstance(file, str):
        raise ValueError("Cannot upload a URL string. Must be a file object.")
    result = cloudinary.uploader.upload(
        file,
        folder=folder,
        public_id=public_id,
        overwrite=True
    )
    return result['public_id'], result['secure_url']


# DELETE IMAGE FROM CLOUDINARY
def delete_from_cloudinary(public_id):
    if not public_id:
        return
    try:
        cloudinary.uploader.destroy(public_id)
    except NotFound:
        pass

# =========================
# AUTH / PUBLIC
# =========================

@main.route("/")
@main.route("/index")
def index():
    if current_user.is_authenticated:
        return redirect(
            url_for("main.seller_dashboard")
            if current_user.role == "seller"
            else url_for("main.select_seller")
        )
    return render_template("index.html")

@main.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user or not user.check_password(form.password.data):
            flash("Invalid credentials", "danger")
            return redirect(url_for("main.login"))

        login_user(user, remember=form.remember.data)
        next_page = request.args.get("next")
        if not next_page or urlparse(next_page).netloc != "":
            return redirect(
                url_for("main.seller_dashboard")
                if user.role == "seller"
                else url_for("main.select_seller")
            )
        return redirect(next_page)

    return render_template("login.html", form=form)

@main.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)

        if user.role == "seller":
            db.session.add(SellerProfile(user_id=user.id))
            db.session.commit()
            return redirect(url_for("main.seller_dashboard"))

        return redirect(url_for("main.select_seller"))

    return render_template("register.html", form=form)

@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.index"))

# =========================
# SELLER DASHBOARD
# =========================

@main.route("/seller/dashboard")
@login_required
def seller_dashboard():
    if current_user.role != "seller":
        flash("Access denied", "danger")
        return redirect(url_for("main.index"))

    products = Product.query.filter_by(seller_id=current_user.id).all()
    categories = Category.query.filter_by(seller_id=current_user.id).all()

    form = CategoryForm()
    form.parent_id.choices = [(0, "No parent")] + [(c.id, c.name) for c in categories]

    return render_template(
        "seller_dashboard.html",
        products=products,
        categories=categories,
        form=form,
        category_form=form
    )



# =========================
# PRODUCT (CLOUDINARY)
# =========================
@main.route("/seller/product/add", methods=["GET", "POST"])
@login_required
def add_product():
    if current_user.role != "seller":
        flash("Access denied", "danger")
        return redirect(url_for("main.index"))

    form = ProductForm()

    # Fetch categories for the seller
    categories = Category.query.filter_by(seller_id=current_user.id).all()
    if not categories:
        uncategorized = Category(name="Uncategorized", seller_id=current_user.id)
        db.session.add(uncategorized)
        db.session.commit()
        categories = [uncategorized]

    form.category_id.choices = [(c.id, c.name) for c in categories]

    # Image fields in the form
    image_fields = [
        form.product_image1, form.product_image2,
        form.product_image3, form.product_image4
    ]

    if form.validate_on_submit():
        # Create product record
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            size_unit=form.size_unit.data,
            stock_quantity=form.stock_quantity.data,
            seller_id=current_user.id,
            category_id=form.category_id.data
        )
        db.session.add(product)
        db.session.commit()  # Commit to get product.id

        # Upload images to Cloudinary
        for i, field in enumerate(image_fields):
            file = field.data
            if isinstance(file, FileStorage) and file.filename:
                # Create a unique public_id per image
                public_id = f"product_{product.id}_{i+1}"

                pid, url = upload_to_cloudinary(
                    file=file,
                    folder=f"products/{product.id}",
                    public_id=public_id
                )

                # Save image record in DB
                db.session.add(
                    ProductImage(
                        product_id=product.id,
                        image_url=url,
                        public_id=pid
                    )
                )

        db.session.commit()
        flash("Product added successfully", "success")
        return redirect(url_for("main.seller_dashboard"))

    return render_template(
        "add_product.html",
        form=form,
        product_image_fields=image_fields
    )


@main.route("/seller/profile/", defaults={"user_id": None}, methods=["GET", "POST"])
@main.route("/seller/profile/<int:user_id>", methods=["GET", "POST"])
@login_required
def seller_profile(user_id):
    # If no user_id is provided, assume current seller wants their own profile
    if user_id is None:
        if current_user.role != "seller":
            flash("Access denied.", "danger")
            return redirect(url_for("main.index"))
        user_id = current_user.id

    profile = SellerProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        flash("Seller profile not found.", "danger")
        return redirect(url_for("main.index"))

    # Only owner seller can edit
    editable = current_user.role == "seller" and current_user.id == profile.user_id

    form = SellerProfileForm(obj=profile) if editable else None

    # Prepare gallery images (4 slots)
    gallery_images = [None, None, None, None]
    existing_images = profile.images.all()
    for i, img in enumerate(existing_images[:4]):
        gallery_images[i] = img

    # Handle form submission only if editable
    if editable and form.validate_on_submit():
        # Update text fields
        profile.shop_name = form.shop_name.data
        profile.about = form.about.data
        profile.phone_number = form.phone_number.data
        profile.location = form.location.data
        profile.open_hours = form.open_hours.data

        # --- SHOP LOGO ---
        file = request.files.get('shop_logo')
        if file and file.filename:
            public_id = f"sellers/logos/{uuid.uuid4().hex}"
            pid, url = upload_to_cloudinary(file, folder="sellers/logos", public_id=public_id)
            profile.shop_logo = url
            profile.shop_logo_public_id = pid

        # --- GALLERY IMAGES (4 slots) ---
        for idx in range(4):
            file_key = f'gallery_{idx}'
            file = request.files.get(file_key)
            if file and file.filename:
                public_id = f"sellers/gallery/{uuid.uuid4().hex}"
                pid, url = upload_to_cloudinary(file, folder="sellers/gallery", public_id=public_id)

                if gallery_images[idx]:
                    # update existing image
                    gallery_images[idx].image_url = url
                    gallery_images[idx].public_id = pid
                else:
                    # create new image
                    new_image = SellerImage(
                        seller_profile_id=profile.id,
                        image_url=url,
                        public_id=pid
                    )
                    db.session.add(new_image)

        db.session.commit()
        flash("Profile updated successfully", "success")
        return redirect(url_for("main.seller_profile", user_id=user_id))

    return render_template(
        "seller_profile.html",
        form=form,
        profile=profile,
        editable=editable,
        gallery_images=gallery_images
    )
    
    
# =========================
# BUYER PROFILE (CLOUDINARY)
# =========================
@main.route('/buyers/sellers')
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

@main.route("/buyer/profile", methods=["GET", "POST"])
@login_required
def buyer_profile():
    if current_user.role != "buyer":
        flash("Access denied", "danger")
        return redirect(url_for("main.index"))

    # Get or create buyer profile
    profile = BuyerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        profile = BuyerProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()

    form = BuyerProfileForm(obj=profile)

    if form.validate_on_submit():
        # Update profile fields
        form.populate_obj(profile)

        # Handle profile image upload
        if form.profile_image.data:
            # Delete old image if exists
            if profile.profile_image_public_id:
                delete_from_cloudinary(profile.profile_image_public_id)

            # Upload new image
            pid, url = upload_to_cloudinary(
                file=form.profile_image.data,
                folder=f"buyers/{current_user.id}/profile",
                public_id=f"profile_{current_user.id}"
            )

            profile.profile_image = url
            profile.profile_image_public_id = pid

        profile.user.last_seen = datetime.utcnow()
        db.session.commit()
        flash("Profile updated successfully ✅", "success")
        return redirect(url_for("main.buyer_profile"))

    return render_template("buyer_profile.html", form=form, profile=profile)

    
@main.route('/cart')
@login_required
def view_cart():
    # Demo page for now
    return "<h1>Cart Page (Demo)</h1>"


@main.route('/payment-method')
@login_required
def payment_method():
    return "<h1>Payment Method Page (Demo)</h1>"

    
@main.route('/buyers/seller/<int:seller_id>/products')
def view_seller_products(seller_id):
    seller = User.query.get_or_404(seller_id)
    products = Product.query.filter_by(seller_id=seller_id).all()
    categories = Category.query.filter_by(seller_id=seller_id).all()
    return render_template('buyers_product.html', seller=seller, products=products, categories= categories)


@main.route('/product/<int:product_id>')
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


@main.route('/product/<int:product_id>/message', methods=['GET', 'POST'])
@login_required
def message_seller(product_id):
    product = Product.query.get_or_404(product_id)

    # Only buyers can send messages
    if current_user.role != 'buyer':
        flash("Only buyers can send messages to sellers.", "danger")
        return redirect(url_for('main.product_detail', product_id=product.id))

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
        return redirect(url_for('main.product_detail', product_id=product.id))

    return render_template('message_form.html', form=form, product=product, seller=seller)

@main.route('/inbox')
@login_required
def inbox():
    products_info = []

    if current_user.role == 'seller':
        # Seller view
        products = Product.query.filter_by(seller_id=current_user.id).all()
        for product in products:
            # get all messages for this product
            messages = Message.query.filter_by(product_id=product.id).order_by(Message.timestamp.desc()).all()

            buyers_dict = {}

            for msg in messages:
                # skip messages sent by seller or invalid product
                if msg.sender_id == current_user.id or not msg.product:
                    continue

                buyer_id = msg.sender_id
                if buyer_id not in buyers_dict:
                    buyers_dict[buyer_id] = {
                        "id": buyer_id,
                        "username": msg.sender.username
                    }

            buyers = list(buyers_dict.values())

            # count only unread messages from buyers
            unread_count = Message.query.filter_by(
                product_id=product.id,
                receiver_id=current_user.id,
                is_read=False
            ).count()

            if buyers:
                products_info.append({
                    "product": product,
                    "buyers": buyers,
                    "unread_messages_count": unread_count
                })

    else:
        # Buyer view
        messages = Message.query.filter(
            (Message.sender_id == current_user.id) |
            (Message.receiver_id == current_user.id)
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
        products_info = list(products_dict.values())

    return render_template('inbox.html', products_info=products_info)

@main.route('/messages/<int:product_id>/<int:user_id>', methods=['GET', 'POST'])
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
            content=form.content.data,
            is_read=False  # mark new messages as unread
        )
        db.session.add(msg)
        db.session.commit()
        return redirect(url_for('main.conversation', product_id=product.id, user_id=other_user.id))

    # Fetch conversation messages
    msgs = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == other_user.id)) |
        ((Message.sender_id == other_user.id) & (Message.receiver_id == current_user.id))
    ).filter_by(product_id=product.id).order_by(Message.timestamp).all()

    # MARK MESSAGES AS READ for seller
    if current_user.role == 'seller':
        for msg in msgs:
            if msg.receiver_id == current_user.id and not msg.is_read:
                msg.is_read = True
        db.session.commit()

    return render_template('conversation.html', messages=msgs, form=form, product=product, other_user=other_user)


@main.route('/forgot-password')
def forgot_password():
    form = ForgotPasswordForm()
    return render_template('forgot_password.html', title='Forgot Password', form=form)

# -------------------------
# RESET PASSWORD PAGE
# -------------------------
@main.route('/reset-password')
def reset_password():
    form = ResetPasswordForm()
    return render_template('reset_password.html', title='Reset Password', form=form)



@main.route('/seller/category/add', methods=['POST'])
@login_required
def quick_add_category():
    if current_user.role != 'seller':
        flash("Access denied.", "danger")
        return redirect(url_for('main.seller_dashboard'))

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
        

    return redirect(url_for('main.seller_dashboard'))

@main.route('/seller/category/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    category = Category.query.get_or_404(id)

    if category.seller_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for('main.seller_dashboard'))

    form = CategoryForm(obj=category)

    form.parent_id.choices = [
        (0, "None")
    ] + [(c.id, c.name) for c in Category.query.filter_by(seller_id=current_user.id)]

    if form.validate_on_submit():
        category.name = form.name.data
        category.parent_id = form.parent_id.data or None
        db.session.commit()
        flash("Category updated!", "success")
        return redirect(url_for('main.seller_dashboard'))

    return render_template('edit_category.html', form=form)



@main.route('/seller/category/<int:id>/delete', methods=['POST'])
@login_required
def delete_category(id):
    category = Category.query.get_or_404(id)

    if category.seller_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for('main.seller_dashboard'))

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
    return redirect(url_for('main.seller_dashboard'))


from flask import current_app
from werkzeug.utils import secure_filename

# ------------------------- EDIT PRODUCT -------------------------
@main.route('/seller/product/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)

    if product.seller_id != current_user.id:
        flash('Access Denied.', 'danger')
        return redirect(url_for('main.seller_dashboard'))

    form = ProductForm()
    # Load seller categories
    categories = Category.query.filter_by(seller_id=current_user.id).all()
    if not categories:
        default_category = Category(name="Uncategorized", seller_id=current_user.id)
        db.session.add(default_category)
        db.session.commit()
        categories = [default_category]
    form.category_id.choices = [(c.id, c.name) for c in categories]

    # Prepare image fields
    product_image_fields = [form.product_image1, form.product_image2, form.product_image3, form.product_image4]
    existing_images = product.images.order_by(ProductImage.id).all()  # ensures order

    # Pre-fill form on GET
    if request.method == 'GET':
        form.name.data = product.name
        form.price.data = product.price
        form.description.data = product.description
        form.size_unit.data = product.size_unit
        form.stock_quantity.data = product.stock_quantity
        form.category_id.data = product.category_id if product.category_id else 0

    if form.validate_on_submit():
        # Update basic fields
        product.name = form.name.data
        product.price = form.price.data
        product.description = form.description.data
        product.size_unit = form.size_unit.data
        product.stock_quantity = form.stock_quantity.data
        product.category_id = form.category_id.data if form.category_id.data != 0 else None

        # Handle Cloudinary uploads
        for idx, field in enumerate(product_image_fields):
            file = field.data
            if file:
                pid, url = upload_to_cloudinary(file, f"products/{product.id}")

                if idx < len(existing_images):
                    # Replace existing
                    old_image = existing_images[idx]
                    delete_from_cloudinary(old_image.public_id)
                    old_image.image_url = url
                    old_image.public_id = pid
                else:
                    # Add new image if less than 4
                    if len(existing_images) < 4:
                        new_img = ProductImage(product_id=product.id, image_url=url, public_id=pid)
                        db.session.add(new_img)

        db.session.commit()
        flash(f'Product "{product.name}" updated successfully!', 'success')
        return redirect(url_for('main.seller_dashboard'))


    return render_template(
        'edit_product.html',
        title=f"Edit Product - {product.name}",
        form=form,
        product=product,
        product_image_fields=product_image_fields,
        existing_images=existing_images
    )


# ------------------------- DELETE PRODUCT -------------------------
@main.route('/seller/product/<int:id>/delete', methods=['POST'])
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    if product.seller_id != current_user.id:
        flash("Access Denied.", "danger")
        return redirect(url_for('main.seller_dashboard'))

    # Delete Cloudinary images first
    for img in product.images:
        delete_from_cloudinary(img.public_id)
        db.session.delete(img)

    db.session.delete(product)
    db.session.commit()
    flash('Product deleted!', 'success')
    return redirect(url_for('main.seller_dashboard'))


# ------------------------- DELETE SINGLE PRODUCT IMAGE -------------------------
@main.route('/seller/product/image/<int:id>/delete', methods=['POST'])
@login_required
def delete_product_image(id):
    image = ProductImage.query.get_or_404(id)
    product = Product.query.get_or_404(image.product_id)

    if product.seller_id != current_user.id:
        flash("Access Denied.", "danger")
        return redirect(url_for('main.seller_dashboard'))

    delete_from_cloudinary(image.public_id)
    db.session.delete(image)
    db.session.commit()
    flash("Image deleted!", "success")
    return redirect(url_for('main.edit_product', id=product.id))
