from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask import current_app as app
from .forms import SignupForm, LoginForm
from ..models import User, db
from .. import login_manager
from flask_login import login_required, login_user, logout_user, current_user

auth_bp = Blueprint('auth', __name__,
                    url_prefix='/auth',
                    template_folder='templates',
                    static_folder='static')


@auth_bp.route('/')
def index():
    return redirect('/auth/login')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home.app'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(password=form.password.data):
            login_user(user)
            return redirect(url_for('home.app'))
        flash('Invalid username or password')
        return redirect(url_for('auth.login'))
    return render_template('auth.html', form=form)
        

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user is None:
            user = User(username=form.username.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('home.app'))
        flash('A user with that username already exists.')
    return render_template('signup.html', form=form)


@login_manager.user_loader
def load_user(user_id):
    if user_id is not None:
        return User.query.get(user_id)
    return None


@login_manager.unauthorized_handler
def unauthorized():
    flash('You must be logged in to view that page.')
    return redirect(url_for('auth.login'))


'''
@auth_bp.route('/login', methods=['GET'])
def login():
    # homepage
    redirect_uri = url_for('authorize', _external=True)
    return oauth.authorize_redirect(redirect_uri)
'''
'''
@auth_bp.route('/authorize')
def authorize():
    token = oauth.authorize_access_token()
'''
