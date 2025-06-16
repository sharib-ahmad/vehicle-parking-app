from models import db
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import enum

# Timezone Configuration
IST = datetime.now().astimezone().tzinfo

# Enums
class UserRole(enum.Enum): ADMIN = "admin"; USER = "user"
class SpotStatus(enum.Enum): AVAILABLE = "A"; OCCUPIED = "O"
class ReservationStatus(enum.Enum): ACTIVE = "active"; COMPLETED = "completed"
class PaymentStatus(enum.Enum): PENDING = "pending"; PAID = "paid"

# User Model
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
    scheduled_delete_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(IST), onupdate=lambda: datetime.now(IST))
    reservations = db.relationship('ReservedParkingSpot', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    vehicles = db.relationship('Vehicle', back_populates='user', cascade='all, delete-orphan')
    profile = db.relationship('UserProfile', back_populates='user', uselist=False, cascade='all, delete')

    @property
    def password(self): raise AttributeError("Password is write-only.")
    @password.setter
    def password(self, plain): self.password_hash = generate_password_hash(plain)
    def check_password(self, plain): return check_password_hash(self.password_hash, plain)
    def is_admin(self): return self.role == UserRole.ADMIN
    def schedule_deletion(self): self.scheduled_delete_at = datetime.now(IST) + timedelta(days=15); self.is_active = False
    def cancel_deletion(self): self.scheduled_delete_at = None; self.is_active = True
    def should_be_deleted(self): return self.scheduled_delete_at and datetime.now(IST) >= self.scheduled_delete_at
    def __repr__(self): return f'<User {self.full_name}>'

# UserProfile
class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.id'), unique=True, nullable=False)
    bio = db.Column(db.Text)
    profile_pic = db.Column(db.String(255))
    date_of_birth = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(IST), onupdate=lambda: datetime.now(IST))
    user = db.relationship('User', back_populates='profile')

# ParkingLot
class ParkingLot(db.Model):
    __tablename__ = 'parking_lots'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    prime_location_name = db.Column(db.String(100), nullable=False)
    price_per_hour = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    pin_code = db.Column(db.String(20), nullable=False)
    floor_level = db.Column(db.Integer, default=1)
    maximum_number_of_spots = db.Column(db.Integer, nullable=False)
    revenue = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    open_time = db.Column(db.Time)
    close_time = db.Column(db.Time)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(IST), onupdate=lambda: datetime.now(IST))
    parking_spots = db.relationship('ParkingSpot', back_populates='parking_lot', lazy='dynamic', cascade='all, delete-orphan')

    def available_spots_count(self): return self.parking_spots.filter_by(status=SpotStatus.AVAILABLE).count()
    @property
    def occupied_spots(self): return self.parking_spots.filter_by(status=SpotStatus.OCCUPIED).count()
    def total_spots_info(self): return f"Occupied: {self.occupied_spots}/{self.maximum_number_of_spots}"
    def __repr__(self): return f'<ParkingLot {self.name}>'

# ParkingSpot
class ParkingSpot(db.Model):
    __tablename__ = 'parking_spots'
    id = db.Column(db.Integer, primary_key=True)
    spot_number = db.Column(db.String(20), nullable=False)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lots.id'), nullable=False)
    status = db.Column(db.Enum(SpotStatus), default=SpotStatus.AVAILABLE, nullable=False)
    is_covered = db.Column(db.Boolean, default=False)
    revenue = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(IST), onupdate=lambda: datetime.now(IST))
    parking_lot = db.relationship('ParkingLot', back_populates='parking_spots')
    reservations = db.relationship('ReservedParkingSpot', back_populates='parking_spot', lazy='dynamic', cascade='save-update')

    def __repr__(self): return f'<ParkingSpot {self.spot_number} in Lot {self.lot_id}>'

# ReservedParkingSpot
class ReservedParkingSpot(db.Model):
    __tablename__ = 'reserved_parking_spots'
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spots.id', ondelete='Set NULL'), nullable=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    vehicle_number = db.Column(db.String(20), db.ForeignKey('vehicles.vehicle_number', ondelete='CASCADE'))
    reservation_timestamp = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    parking_timestamp = db.Column(db.DateTime(timezone=True))
    leaving_timestamp = db.Column(db.DateTime(timezone=True))
    parking_cost_per_hour = db.Column(db.Float, nullable=False)
    status = db.Column(db.Enum(ReservationStatus), default=ReservationStatus.ACTIVE)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(IST), onupdate=lambda: datetime.now(IST))
    user = db.relationship('User', back_populates='reservations')
    parking_spot = db.relationship('ParkingSpot', back_populates='reservations')
    vehicle = db.relationship('Vehicle', back_populates='reservations', uselist=False)
    payment = db.relationship('Payment', back_populates='reservation', uselist=False)
    def __repr__(self): return f'<Reservation ID={self.id} Spot={self.spot_id} User={self.user_id}>'

# Payment
class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reserved_parking_spots.id', ondelete='CASCADE'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    payment_status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_timestamp = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(IST), onupdate=lambda: datetime.now(IST))
    reservation = db.relationship('ReservedParkingSpot', back_populates='payment')
    def __repr__(self): return f'<Payment ID={self.id} Reservation={self.reservation_id}>'

# Vehicle
class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    vehicle_number = db.Column(db.String(20), primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    fuel_type = db.Column(db.String(10), nullable=False)
    brand = db.Column(db.String(50))
    model = db.Column(db.String(50))
    color = db.Column(db.String(30))
    registration_date = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    is_active = db.Column(db.Boolean, default=True)
    user = db.relationship('User', back_populates='vehicles')
    reservations = db.relationship('ReservedParkingSpot', back_populates='vehicle', cascade='all, delete-orphan')
    def __repr__(self): return f"<Vehicle {self.vehicle_number}>"

# Automatic Admin Creation
def create_admin_user(app):
    with app.app_context():
        if not User.query.filter_by(role=UserRole.ADMIN).first():
            try:
                admin = User(
                    id='@sharib123',
                    full_name='Sharib Ahmad',
                    email='sharib@gmail.com',
                    password_hash=generate_password_hash('admin123'),
                    phone_number='1234567890',
                    address='123 Admin St, Admin City',
                    pin_code='123456',
                    role=UserRole.ADMIN,
                    is_active=True
                )
                db.session.add(admin)
                db.session.commit()
                current_app.logger.info(f'Admin created successfully: {admin.full_name}')
            except SQLAlchemyError:
                db.session.rollback()
                current_app.logger.error('Error occurred during automatic admin creation')
            finally:
                db.session.close()
