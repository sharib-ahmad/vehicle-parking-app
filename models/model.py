from models import db
from flask import current_app
from flask_login import UserMixin
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
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


# Function to create admin user when database is initialized
def create_admin_user(app):
    with app.app_context():
        if not User.query.filter_by(role=UserRole.ADMIN).first():
            try:
                admin = User(
                    id = '@sharib123',
                    full_name='Sharib Ahmad',
                    email = 'sharib@gmail.com',
                    password_hash=generate_password_hash('admin123'),  # Use a secure password
                    phone_number='1234567890',
                    address='123 Admin St, Admin City',
                    pin_code='123456',
                    role=UserRole.ADMIN,
                    is_active=True

                )
                db.session.add(admin)
                db.session.commit()
                current_app.logger.info(f'admin created successfully {admin.id}')
            except SQLAlchemyError as e:
                db.session.rollback()
                current_app.logger.error(f'error occured during created automatic admin to database {str(e)}')

            finally:
                db.session.close() 

