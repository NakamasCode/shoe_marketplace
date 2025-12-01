from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, FloatField, IntegerField
from wtforms.validators import DataRequired, Email, ValidationError, EqualTo, Length, NumberRange, Regexp
from app.models import User
from flask_wtf.file import FileField, FileAllowed, MultipleFileField


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')
    

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('buyer', 'Buyer'), ('seller', 'Seller')], validators=[DataRequired()])
    submit = SubmitField('Sign Up')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Please use a different username.')
        
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Please use a different email address.')


class SellerProfileForm(FlaskForm):
    shop_name = StringField('Shop Name', validators=[DataRequired()])
    about = TextAreaField('About your shop', validators=[Length(max=200)])
    phone_number = StringField(
        'Phone Number', 
        validators=[DataRequired(), Regexp(r'^\+?\d{10,15}$', message="Enter a valid phone number.")]
    )
    location = StringField('Location', validators=[DataRequired()])
    open_hours = StringField('Open Hours', validators=[Length(max=50)])
    shop_logo = FileField('Upload Shop Logo', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    
    # Added field for gallery images
    gallery_image1 = FileField('Gallery Image 1', validators=[FileAllowed(['jpg','png','jpeg'],'Images only!')])
    gallery_image2 = FileField('Gallery Image 2', validators=[FileAllowed(['jpg','png','jpeg'],'Images only!')])
    gallery_image3 = FileField('Gallery Image 3', validators=[FileAllowed(['jpg','png','jpeg'],'Images only!')])
    gallery_image4 = FileField('Gallery Image 4', validators=[FileAllowed(['jpg','png','jpeg'],'Images only!')])
    
    submit = SubmitField('Save Profile')


class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired()])
    parent_id = SelectField('Parent Category', coerce=int, choices=[])  # Populate dynamically in route
    submit = SubmitField('Save Category')


class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Length(max=500)])
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    size_unit = StringField('Size/Unit', validators=[Length(max=20)])
    stock_quantity = IntegerField('Stock Quantity', validators=[DataRequired(), NumberRange(min=0)])

    # Gallery images (just like seller)
    product_image1 = FileField('Product Image 1', validators=[FileAllowed(['jpg','png','jpeg'],'Images only!')])
    product_image2 = FileField('Product Image 2', validators=[FileAllowed(['jpg','png','jpeg'],'Images only!')])
    product_image3 = FileField('Product Image 3', validators=[FileAllowed(['jpg','png','jpeg'],'Images only!')])
    product_image4 = FileField('Product Image 4', validators=[FileAllowed(['jpg','png','jpeg'],'Images only!')])

    submit = SubmitField('Save Product')


class DeleteForm(FlaskForm):
    submit = SubmitField('Delete')