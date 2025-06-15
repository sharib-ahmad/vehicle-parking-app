"""
# Models Package Initialization
# This module initializes the Flask extensions and imports models and forms for the application.
# It sets up SQLAlchemy, Flask-Login, CSRF protection, and Flask-RESTful.
"""

from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect


# Flask Extensions
# Initializes extensions for database, authentication, and CSRF protection.

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


# Model Imports
# Imports all database models for use throughout the application.

from .model import (
    User, UserRole, SpotStatus, ParkingLot, ReservedParkingSpot, ParkingSpot,
    create_admin_user, Vehicle, IST, ReservationStatus, Payment, PaymentStatus, UserProfile
)


# Form Imports
# Imports all Flask-WTF forms for user input validation.

from .forms import (
    RegistrationForm, LoginForm, ParkingLotForm, EditParkingLotForm, CsrfOnlyForms,
    ReservedSpotForm, UserSearchForm, AdminSearchForm, ReleasedForm, PaymentForm,
    DeleteParkingSpotForm, ProfileForm
)

# End of Models Package Initialization