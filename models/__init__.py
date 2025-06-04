from flask_sqlalchemy import SQLAlchemy



db = SQLAlchemy()


from .model import UserRole, User 
from .form import RegistrationForm