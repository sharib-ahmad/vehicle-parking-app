"""
# Models Package Initialization
# This module initializes the Flask extensions and imports models and forms for the application.
# It sets up SQLAlchemy, Flask-Login, CSRF protection, and Flask-RESTful.
"""

from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

# Flask Extensions
# Initializes extensions for database, authentication, and CSRF protection.

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()



# End of Models Package Initialization
