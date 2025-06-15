"""
# API Controller
# This module defines the RESTful API endpoints for managing users, parking lots, parking spots,
# and vehicles. It includes authentication and authorization checks to ensure secure access.
"""

import random
from datetime import datetime
from functools import wraps

from flask import Blueprint, current_app
from flask_login import current_user, login_required
from flask_restful import Api, Resource, abort, fields, marshal_with, reqparse
from werkzeug.security import check_password_hash, generate_password_hash

from models import (ParkingLot, ParkingSpot, SpotStatus, User, UserRole,
                    Vehicle, db)

# Blueprint and API Initialization
# Sets up the API blueprint and Flask-RESTful integration.

api_bp = Blueprint('api', __name__)
api = Api(api_bp)

# Decorators
# Defines custom decorators for restricting access to admin users.

def admin_required(f):
    """Restricts access to admin users only."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401, message="Authentication required")
        if not current_user.is_admin():
            abort(403, message="Admin access required")
        return f(*args, **kwargs)
    return decorated_function

# User API Resource
# Manages user-related operations such as fetching, creating, updating, and deleting users.

# Request Parser for User
user_args = reqparse.RequestParser()
user_args.add_argument('full_name', type=str, required=True, help="Full name is required")
user_args.add_argument('email', type=str, required=True, help="Email is required")
user_args.add_argument('password', type=str, required=True, help="Password is required")
user_args.add_argument('phone_number', type=str)
user_args.add_argument('address', type=str)
user_args.add_argument('pin_code', type=str)

# Output Fields for User
user_fields = {
    'id': fields.String,
    'full_name': fields.String,
    'email': fields.String,
    'phone_number': fields.String,
    'address': fields.String,
    'pin_code': fields.String,
    'is_active': fields.Boolean,
    'created_at': fields.DateTime(dt_format='iso8601'),
    'updated_at': fields.DateTime(dt_format='iso8601')
}

class UserApi(Resource):
    @marshal_with(user_fields)
    @admin_required
    def get(self, user_id=None):
        """Fetches a single user or all users."""
        if user_id:
            user = User.query.get(user_id)
            if not user:
                abort(404, message="User not found")
            return user
        else:
            return User.query.filter_by(role=UserRole.USER).all()

    @marshal_with(user_fields)
    def post(self):
        """Creates a new user."""
        args = user_args.parse_args()
        if User.query.filter_by(email=args['email']).first():
            abort(400, message="Email already exists")

        new_user = User(
            id='@' + args['email'].split('@')[0] + str(random.randint(100, 999)),
            full_name=args['full_name'],
            email=args['email'],
            password_hash=generate_password_hash(args['password']),
            phone_number=args.get('phone_number'),
            address=args.get('address'),
            pin_code=args.get('pin_code')
        )
        db.session.add(new_user)
        db.session.commit()
        return new_user, 201

    @marshal_with(user_fields)
    @login_required
    def put(self, user_id):
        """Updates a user's information."""
        args = user_args.parse_args()
        user = User.query.get(user_id)
        if not user:
            abort(404, message="User not found")

        user.full_name = args['full_name']
        user.phone_number = args.get('phone_number')
        user.address = args.get('address')
        user.pin_code = args.get('pin_code')
        if args.get('password'):
            user.password_hash = generate_password_hash(args['password'])

        db.session.commit()
        return user, 200

    @admin_required
    def delete(self, user_id):
        """Deletes a user."""
        user = User.query.get(user_id)
        if not user:
            abort(404, message="User not found")

        db.session.delete(user)
        db.session.commit()
        return {"message": "User deleted successfully"}, 200

# Parking Lot API Resource
# Manages parking lot operations such as fetching, creating, updating, and deleting parking lots.

# Request Parser for Parking Lot
parking_args = reqparse.RequestParser()
parking_args.add_argument('name', type=str, required=True, help='Name is required')
parking_args.add_argument('prime_location_name', type=str, required=True, help='Prime location name is required')
parking_args.add_argument('price_per_hour', type=float, required=True, help='Price per hour is required')
parking_args.add_argument('address', type=str, required=True, help='Address is required')
parking_args.add_argument('pin_code', type=str, required=True, help='Pin code is required')
parking_args.add_argument('floor_level', type=int)
parking_args.add_argument('maximum_number_of_spots', type=int,
                          required=True, help='Maximum number of spots is required')
parking_args.add_argument('is_active', type=bool)
parking_args.add_argument('open_time', type=str)
parking_args.add_argument('close_time', type=str)

# Output Fields for Parking Lot
parking_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'prime_location_name': fields.String,
    'price_per_hour': fields.Float,
    'address': fields.String,
    'pin_code': fields.String,
    'floor_level': fields.Integer,
    'maximum_number_of_spots': fields.Integer,
    'revenue': fields.Float,
    'is_active': fields.Boolean,
    'open_time': fields.String,
    'close_time': fields.String,
    'created_at': fields.DateTime(dt_format='iso8601'),
    'updated_at': fields.DateTime(dt_format='iso8601')
}

class ParkingLotApi(Resource):
    @marshal_with(parking_fields)
    def get(self, lot_id=None):
        """Fetches a single parking lot or all parking lots."""
        if lot_id:
            lot = ParkingLot.query.get(lot_id)
            if not lot:
                abort(404, message="Parking lot not found")
            return lot
        else:
            return ParkingLot.query.all()

    @marshal_with(parking_fields)
    @admin_required
    def post(self):
        """Creates a new parking lot."""
        args = parking_args.parse_args()
        new_lot = ParkingLot(
            name=args['name'],
            prime_location_name=args['prime_location_name'],
            price_per_hour=args['price_per_hour'],
            address=args['address'],
            pin_code=args['pin_code'],
            floor_level=args.get('floor_level', 1),
            maximum_number_of_spots=args['maximum_number_of_spots'],
            is_active=args.get('is_active', True),
            open_time=datetime.strptime(args['open_time'], "%H:%M").time() if args.get('open_time') else None,
            close_time=datetime.strptime(
                args['close_time'], "%H:%M").time() if args.get('close_time') else None
        )
        db.session.add(new_lot)
        db.session.commit()
        return new_lot, 201

    @marshal_with(parking_fields)
    @admin_required
    def put(self, lot_id):
        """Updates a parking lot's information."""
        args = parking_args.parse_args()
        lot = ParkingLot.query.get(lot_id)
        if not lot:
            abort(404, message="Parking lot not found")

        for key, value in args.items():
            if value is not None:
                setattr(lot, key, value)

        db.session.commit()
        return lot, 200

    @admin_required
    def delete(self, lot_id):
        """Deletes a parking lot."""
        lot = ParkingLot.query.get(lot_id)
        if not lot:
            abort(404, message="Parking lot not found")

        db.session.delete(lot)
        db.session.commit()
        return {'message': 'Parking lot deleted successfully'}, 200

# Parking Spot API Resource
# Manages parking spot operations such as fetching, updating, and deleting parking spots.

# Request Parser for Parking Spot
spot_args = reqparse.RequestParser()
spot_args.add_argument('spot_number', type=str, required=True, help='Spot number is required')
spot_args.add_argument('lot_id', type=int, required=True, help='Parking lot ID is required')
spot_args.add_argument('status', type=str, choices=[s.name for s in SpotStatus], help='Invalid status')
spot_args.add_argument('is_covered', type=bool)
spot_args.add_argument('is_active', type=bool)

# Output Fields for Parking Spot
spot_fields = {
    'id': fields.Integer,
    'spot_number': fields.String,
    'lot_id': fields.Integer,
    'status': fields.String(attribute=lambda x: x.status.name),
    'is_covered': fields.Boolean,
    'revenue': fields.Float,
    'is_active': fields.Boolean,
    'created_at': fields.DateTime(dt_format='iso8601'),
    'updated_at': fields.DateTime(dt_format='iso8601'),
}

class ParkingSpotApi(Resource):
    @marshal_with(spot_fields)
    def get(self, spot_id=None):
        """Fetches a single parking spot or all parking spots."""
        if spot_id:
            spot = ParkingSpot.query.get(spot_id)
            if not spot:
                abort(404, message="Parking spot not found")
            return spot
        else:
            return ParkingSpot.query.all()

    @marshal_with(spot_fields)
    @admin_required
    def put(self, spot_id):
        """Updates a parking spot's information."""
        args = spot_args.parse_args()
        spot = ParkingSpot.query.get(spot_id)
        if not spot:
            abort(404, message="Parking spot not found")

        for key, value in args.items():
            if value is not None:
                setattr(spot, key, value)

        db.session.commit()
        return spot, 200

    @admin_required
    def delete(self, spot_id):
        """Deletes a parking spot."""
        spot = ParkingSpot.query.get(spot_id)
        if not spot:
            abort(404, message="Parking spot not found")

        db.session.delete(spot)
        db.session.commit()
        return {'message': 'Parking spot deleted successfully'}, 200

# Vehicle API Resource
# Manages vehicle operations such as fetching, creating, updating, and deleting vehicles.

# Request Parser for Vehicle
vehicle_args = reqparse.RequestParser()
vehicle_args.add_argument('vehicle_number', type=str, required=True, help='Vehicle number is required')
vehicle_args.add_argument('fuel_type', type=str, required=True, help='Fuel type is required')
vehicle_args.add_argument('user_id', type=int, required=True, help='User ID is required')
vehicle_args.add_argument('color', type=str, required=True, help='Color is required')
vehicle_args.add_argument('model', type=str, required=True, help='Model is required')
vehicle_args.add_argument('brand', type=str, required=True, help='Brand is required')

# Output Fields for Vehicle
vehicle_fields = {
    'vehicle_number': fields.String,
    'fuel_type': fields.String,
    'user_id': fields.String,
    'color': fields.String,
    'model': fields.String,
    'brand': fields.String,
}

class VehicleApi(Resource):
    @marshal_with(vehicle_fields)
    @login_required
    def get(self, vehicle_number=None):
        """Fetches a single vehicle or all vehicles."""
        if vehicle_number:
            vehicle = Vehicle.query.get(vehicle_number)
            if not vehicle:
                abort(404, message="Vehicle not found")
            if not current_user.is_admin() and vehicle.user_id != current_user.id:
                abort(403, message="Not authorized to view this vehicle")
            return vehicle
        else:
            if current_user.is_admin():
                return Vehicle.query.all()
            return Vehicle.query.filter_by(user_id=current_user.id).all()

    @marshal_with(vehicle_fields)
    @login_required
    def post(self):
        """Creates a new vehicle."""
        args = vehicle_args.parse_args()
        if Vehicle.query.get(args['vehicle_number']):
            abort(400, message="Vehicle already exists")
        if not current_user.is_admin() and args['user_id'] != current_user.id:
            abort(403, message="You can only register your own vehicle")

        new_vehicle = Vehicle(**args)
        db.session.add(new_vehicle)
        db.session.commit()
        return new_vehicle, 201

    @marshal_with(vehicle_fields)
    @login_required
    def put(self, vehicle_number):
        """Updates a vehicle's information."""
        args = vehicle_args.parse_args()
        vehicle = Vehicle.query.get(vehicle_number)
        if not vehicle:
            abort(404, message="Vehicle not found")
        if not current_user.is_admin() and vehicle.user_id != current_user.id:
            abort(403, message="Not authorized to update this vehicle")

        for key, value in args.items():
            if value is not None and key != 'user_id':
                setattr(vehicle, key, value)
        if current_user.is_admin():
            vehicle.user_id = args['user_id']

        db.session.commit()
        return vehicle, 200

    @admin_required
    def delete(self, vehicle_number):
        """Deletes a vehicle."""
        vehicle = Vehicle.query.get(vehicle_number)
        if not vehicle:
            abort(404, message="Vehicle not found")

        db.session.delete(vehicle)
        db.session.commit()
        return {'message': f'Vehicle {vehicle_number} deleted successfully'}, 200

# API Resource Routing
# Registers API resources with their respective endpoints.

api.add_resource(UserApi, '/users', '/user/<string:user_id>')
api.add_resource(ParkingLotApi, '/parking-lots', '/parking-lot/<int:lot_id>')
api.add_resource(ParkingSpotApi, '/parking-spots', '/parking-spot/<int:spot_id>')
api.add_resource(VehicleApi, '/vehicles', '/vehicle/<string:vehicle_number>')

# End of API Controller