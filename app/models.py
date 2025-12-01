from app import db, login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


# ----------------------
# USER
# ----------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(10))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    seller_profile = db.relationship('SellerProfile', backref='user', uselist=False)
    products = db.relationship('Product', backref='seller', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} | Role: {self.role}>'


# ----------------------
# SELLER PROFILE
# ----------------------
class SellerProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True)

    shop_name = db.Column(db.String(140))
    shop_logo = db.Column(db.String(200))
    about = db.Column(db.Text)
    phone_number = db.Column(db.String(20))
    location = db.Column(db.String(200))
    open_hours = db.Column(db.String(50))
    rating = db.Column(db.Float, default=0.0)

    images = db.relationship('SellerImage', backref='seller_profile', lazy='dynamic')

    def __repr__(self):
        return f'<SellerProfile {self.shop_name}>'


# ----------------------
# SELLER IMAGES
# ----------------------
class SellerImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seller_profile_id = db.Column(db.Integer, db.ForeignKey('seller_profile.id'))
    image_url = db.Column(db.String(200))
    description = db.Column(db.String(200))


# ----------------------
# CATEGORY
# ----------------------
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)

    # NEW → link category to the seller who created it
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Nested categories (optional)
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    children = db.relationship(
        'Category',
        backref=db.backref('parent', remote_side=[id]),
        lazy='dynamic'
    )

    products = db.relationship('Product', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'


# ----------------------
# PRODUCT
# ----------------------
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    size_unit = db.Column(db.String(20))
    stock_quantity = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))

    images = db.relationship('ProductImage', backref='product', lazy='dynamic')

    def __repr__(self):
        return f'<Product {self.name}>'


# ----------------------
# PRODUCT IMAGES
# ----------------------
class ProductImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    image_url = db.Column(db.String(200))
    description = db.Column(db.String(200))


# ----------------------
# LOGIN LOADER
# ----------------------
@login.user_loader
def load_user(id):
    return User.query.get(int(id))
