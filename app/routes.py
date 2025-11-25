from flask import render_template, url_for, redirect, flash, request
from app import app, db
from app.forms import LoginForm, RegisterForm
from flask_login import current_user, login_user,logout_user, login_required
from app.models import User
from urllib.parse import urlparse


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember.data)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            if user.role == 'seller':
                return redirect(url_for('seller_dashboard'))
            else:
                return redirect(url_for('buyer_dashboard'))
        
        
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
        flash('Congratulations, you are now a registered user!')
        login_user(user)
        if form.role.data == 'seller':
            return redirect(url_for('seller_dashboard'))
        else:
            return redirect(url_for('buyer_dashboard'))
    return render_template('register.html', title='Register', form=form)

@app.route('/seller/dashboard')
@login_required
def seller_dashboard():
    # Optional: restrict only sellers
    if current_user.role != 'seller':
        flash("Access denied.")
        return redirect(url_for('index'))
    
    return render_template('seller_dashboard.html', title='Dashboard')


@app.route('/buyer/dashboard')
@login_required
def buyer_dashboard():
    if current_user.role != 'buyer':
        flash('Access Denied.')
        return redirect(url_for('index'))
    return render_template('buyer_dashboard.html', title='Dashboard')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index')) 