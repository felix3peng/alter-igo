from flask import Flask, redirect, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth

# initialize plugins
db = SQLAlchemy()
login_manager = LoginManager()
'''
oauth = OAuth()
'''
def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')

    # write plugins to app
    db.init_app(app)
    login_manager.init_app(app)
    '''
    oauth.init_app(app)

    # set up oauth client
    oauth.register(
        name='',
        client_id='',
        client_secret='',
        api_base_url='',
        access_token_url='',
        authorize_url='',
    )
    '''

    with app.app_context():
        # import and register routes from blueprints
        from .home import home
        from .auth import auth, forms
        app.register_blueprint(home.home_bp)
        app.register_blueprint(auth.auth_bp)

        db.create_all()

        # basic route to redirect to home page
        @app.route('/')
        def index():
            return redirect('/home')
        

        return app
        
