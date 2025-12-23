from app import app, db

from app.models import (
    User,
    SellerProfile,
    SellerImage,
    Category,
    Product,
    ProductImage
)

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User, 
        'SellerProfile': SellerProfile,
        'SellerImage': SellerImage,
        'Category': Category,
        'Product': Product,
        'ProductImage': ProductImage
}




# Automatically create all tables if they don't exist
with app.app_context():
    db.create_all()
