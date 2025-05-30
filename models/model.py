from models import db
from flask_login import UserMixin
from datetime import datetime, timedelta
import enum

IST = datetime.now().astimezone().tzinfo

class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.String(50), primary_key=True)
    full_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(15))
    address = db.Column(db.String(255))
    pin_code = db.Column(db.String(10))
    role = db.Column(db.Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(IST), onupdate=lambda: datetime.now(IST))

    def __repr__(self):
        return f'<User {self.full_name}>'



