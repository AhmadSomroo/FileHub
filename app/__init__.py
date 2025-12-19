# -*- coding: utf-8 -*-
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from .config import Config

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

def create_app(config_object=None):
    app = Flask(__name__, static_folder="static", template_folder="templates")
    
    # Load config
    app_config = Config() if config_object is None else config_object
    app.config.from_object(app_config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    limiter.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    # Force password change for first-time users
    @app.before_request
    def check_first_login():
        from flask import request, redirect, url_for
        from flask_login import current_user
        
        # Skip check for static files, login, logout, and change-password routes
        if request.endpoint and (
            request.endpoint.startswith('static') or
            request.endpoint == 'auth.login' or
            request.endpoint == 'auth.logout' or
            request.endpoint == 'auth.change_password'
        ):
            return
        
        # If user is authenticated and hasn't changed their first password
        if current_user.is_authenticated and current_user.first_login:
            return redirect(url_for('auth.change_password'))
    
    # Security headers middleware
    @app.after_request
    def add_security_headers(response):
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        # XSS Protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # Content Security Policy
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self';"
        )
        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        # Permissions Policy
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response

    # Blueprints - only import and register once
    from .auth import auth_bp
    from .files import files_bp
    from .admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(files_bp)  # only here, remove earlier registration
    app.register_blueprint(admin_bp)

    # Create upload directory if it doesn't exist
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    return app
