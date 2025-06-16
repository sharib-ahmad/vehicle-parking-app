"""
# Controllers Package Initialization
# This module initializes the Flask application by registering all blueprints for routing.
# It centralizes the registration of authentication, user, admin, API, and public page controllers.
"""

from .admin import admin_bp
from .api import api_bp
from .auth import auth_bp
from .local import local_bp
from .user import user_bp

def register_blueprints(app):
    """
    Registers all application blueprints.
    Blueprints registered:
    - auth_bp: Handles authentication (login, register, logout)
    - user_bp: Manages user dashboard and operations
    - admin_bp: Controls admin panel and management
    - api_bp: Provides REST API endpoints
    - local_bp: Serves local/public pages
    Args:
        app (Flask): The main Flask application instance
    """
    
    # Authentication Blueprint
    app.register_blueprint(auth_bp)
    
    # User Blueprint
    app.register_blueprint(user_bp, url_prefix='/user')
    
    # Admin Blueprint
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # API Blueprint
    app.register_blueprint(api_bp, url_prefix='/api')
    app.logger.info("API resources registered successfully")
    
    # Local/Public Blueprint
    app.register_blueprint(local_bp)

# End of Controllers Initialization