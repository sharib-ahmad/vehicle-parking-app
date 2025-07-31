"""
Vehicle Parking Management System - Application Factory
Author: Sharib Ahmad
Roll.no: 24f2001786
"""

import logging
import os
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint

from controllers import api_bp, register_blueprints
from models import csrf, db, login_manager
from models.model import User, create_admin_user

def create_app():
    """Application factory to create and configure the Flask app."""
    load_dotenv()
    app = Flask(__name__)


    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")


    # Extensions Initialization
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    CORS(app)

    # Blueprint Registration
    register_blueprints(app)
    csrf.exempt(api_bp)  # Exclude API from CSRF protection
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        """
        User loader for Flask-Login.
        Loads a user from the database for session management.
        """
        return User.query.get(user_id)

    # Logging Configuration
    if not os.path.exists("logs"):
        os.mkdir("logs")

    file_handler = RotatingFileHandler("logs/app.log", maxBytes=10240, backupCount=3)
    file_handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
    )
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info("🚀 App started and logging is set up.")

    # Database & Admin User Creation
    
    with app.app_context():
        db.create_all()
        create_admin_user(app,email=os.environ.get("ADMIN_EMAIL"),password=os.environ.get("ADMIN_PASSWORD"))

    # Swagger UI for API Documentation
    SWAGGER_URL = "/swagger"
    API_URL = "/static/swagger.yaml"
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL, API_URL, config={"app_name": "Parking API Swagger UI"}
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
    app.static_folder = "static"

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('not_found.html'), 404

    return app

from app import create_app

if __name__ == "__main__":
    app = create_app()
    print(
        """
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                    🚗 VEHICLE PARKING MANAGEMENT SYSTEM                      ║
    ║                         Starting Flask Application...                        ║
    ║                                                                              ║
    ║                    Server: http://localhost:5000                             ║
    ║                    Swagger: http://localhost:5000/swagger                    ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
    """
    )
    app.run()