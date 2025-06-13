from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect


db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

from .model import UserRole, User, create_admin_user, ParkingLot, SpotStatus

from .form import RegistrationForm, LoginForm, CsrfOnlyForms, ParkingLotForm, EditParkingLotForm, UserSearchForm