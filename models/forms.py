"""
# Forms Module
# This module defines Flask-WTF forms for user input validation and rendering in the application.
# Each form corresponds to a specific user or admin action, such as registration, login, or parking lot management.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField, SelectField, IntegerField, FloatField,
    TextAreaField, TimeField, DateTimeField, HiddenField, DateField, FileField
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, ValidationError, NumberRange
)
from models import User


# User Registration Form
# Validates user input for creating a new account.

class RegistrationForm(FlaskForm):
    """Form for user registration with email and phone number uniqueness validation."""

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email.')
        
    def validate_phone_number(self, phone_number):
        user = User.query.filter_by(phone_number=phone_number.data).first()
        if user:
            raise ValidationError('Phone number already registered. Please use a different phone number.')

    full_name = StringField(label='Full Name', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField(
        label='Email',
        filters=[lambda x: x.strip() if x else x],
        validators=[DataRequired(), Email()]
    )
    password_hash = PasswordField(label='Password', validators=[DataRequired()])
    confirm_password = PasswordField(
        label='Confirm Password',
        validators=[DataRequired(), EqualTo('password_hash')]
    )
    phone_number = StringField(
        label='Phone Number',
        validators=[DataRequired(), Length(min=10, max=15)]
    )
    address = StringField(label='Address', validators=[DataRequired()])
    pin_code = StringField(
        label='Pin Code',
        validators=[DataRequired(), Length(min=6, max=10)]
    )
    submit = SubmitField(label='Register')


# User Login Form
# Validates credentials for user login.

class LoginForm(FlaskForm):
    """Form for user login with email and password validation."""

    email = StringField(label='Registered Email Id', validators=[DataRequired(), Email()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    submit = SubmitField(label='Login')


# Parking Lot Creation Form
# Validates input for creating a new parking lot.

class ParkingLotForm(FlaskForm):
    """Form for creating a new parking lot with required fields."""

    name = StringField('Name', validators=[DataRequired()])
    prime_location_name = StringField(label='Prime Location Name', validators=[DataRequired()])
    price_per_hour = FloatField(
        label='Price per Hour',
        validators=[DataRequired(), NumberRange(min=0)]
    )
    address = TextAreaField(label='Address', validators=[DataRequired()])
    pin_code = StringField(label='Pin Code', validators=[DataRequired()])
    floor_level = SelectField(
        label='Floor Level',
        choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')],
        validators=[DataRequired()]
    )
    maximum_number_of_spots = IntegerField(
        label='Maximum Number of Spots',
        validators=[DataRequired(), NumberRange(min=1)]
    )
    open_time = TimeField(label='Open Time', format='%H:%M')
    close_time = TimeField(label='Close Time', format='%H:%M')
    submit = SubmitField(label='Add Lot')


# Parking Lot Edit Form
# Validates input for updating an existing parking lot.

class EditParkingLotForm(FlaskForm):
    """Form for editing parking lot details with some read-only fields."""

    name = StringField(
        label='Name',
        validators=[DataRequired()],
        render_kw={'readonly': True}
    )
    prime_location_name = StringField(
        label='Prime Location',
        validators=[DataRequired()],
        render_kw={'readonly': True}
    )
    price_per_hour = FloatField(
        label='Price per Hour',
        validators=[DataRequired(), NumberRange(min=0)]
    )
    address = StringField(
        label='Address',
        validators=[DataRequired()],
        render_kw={'readonly': True}
    )
    pin_code = StringField(
        label='Pin Code',
        validators=[DataRequired()],
        render_kw={'readonly': True}
    )
    floor_level = SelectField(
        label='Floor Level',
        choices=[],
        validators=[DataRequired()],
        render_kw={'readonly': True}
    )
    open_time = TimeField(label='Open Time', format='%H:%M')
    close_time = TimeField(label='Close Time', format='%H:%M')
    is_active = SelectField(
        label='Active',
        validators=[DataRequired()],
        choices=[('true', 'True'), ('false', 'False')]
    )
    maximum_number_of_spots = IntegerField(
        label='Max Number of Spots',
        validators=[DataRequired(), NumberRange(min=1)],
        render_kw={'readonly': True}
    )
    submit = SubmitField(label='Update')


# Parking Spot Reservation Form
# Validates input for reserving a parking spot and registering a vehicle.

class ReservedSpotForm(FlaskForm):
    """Form for reserving a parking spot and registering vehicle details."""

    spot_id = StringField(
        label='Spot Id',
        validators=[DataRequired()],
        render_kw={'readonly': True}
    )
    user_id = StringField(
        label='User Id',
        validators=[DataRequired()],
        render_kw={'readonly': True}
    )
    lot_id = StringField(
        label='Lot Id',
        validators=[DataRequired()],
        render_kw={'readonly': True}
    )
    vehicle_number = StringField(label='Vehicle Number', validators=[DataRequired()])
    fuel_type = SelectField(
        label="Fuel Type",
        choices=[
            ("petrol", "Petrol"),
            ("diesel", "Diesel"),
            ("electric", "Electric"),
        ],
        validators=[DataRequired()]
    )
    brand = SelectField(label="Brand", choices=[], validators=[DataRequired()])
    model = SelectField(label="Model", choices=[], validators=[DataRequired()])
    color = SelectField(label='Color', choices=[], validators=[DataRequired()])
    submit = SubmitField(label="Register Vehicle")


# User Search Form
# Validates input for searching parking lots by location.

class UserSearchForm(FlaskForm):
    """Form for users to search parking lots by location."""

    location = StringField(label='Search by Location', validators=[DataRequired()])
    submit = SubmitField(label='Search')


# Admin Search Form
# Validates input for admin searches across multiple criteria.

class AdminSearchForm(FlaskForm):
    """Form for admin searches by various criteria like user ID, email, or vehicle number."""

    search_by = SelectField(
        label='Search by',
        choices=[
            ('user_id', 'User ID'),
            ('full_name', 'Full Name'),
            ('email', 'Email'),
            ('phone_number', 'Phone Number'),
            ('location', 'Location'),
            ('vehicle_number', 'Vehicle Number'),
            ('pin_code', 'Pin Code')
        ]
    )
    search_value = StringField(label='Search string', validators=[DataRequired()])
    submit = SubmitField(label='Search')


# Vehicle Release Form
# Validates input for releasing a parked vehicle.

class ReleasedForm(FlaskForm):
    """Form for releasing a vehicle from a parking spot with calculated duration and cost."""

    user_id = StringField(
        label='User ID',
        validators=[DataRequired()],
        render_kw={'readonly': True}
    )
    spot_id = StringField(
        label='Spot ID',
        validators=[DataRequired()],
        render_kw={'readonly': True}
    )
    vehicle_number = StringField(
        label='Vehicle Number',
        validators=[DataRequired()],
        render_kw={'readonly': True}
    )
    parking_timestamp = DateTimeField(
        label='Parking Time',
        validators=[DataRequired()],
        format='%Y-%m-%d %H:%M:%S',
        render_kw={'readonly': True}
    )
    leaving_timestamp = DateTimeField(
        label='Leaving Time',
        validators=[DataRequired()],
        format='%Y-%m-%d %H:%M:%S',
        render_kw={'readonly': True}
    )
    duration = StringField(label='Total Duration In Hour(s)', render_kw={'readonly': True})
    total_cost = StringField(label='Total Cost', render_kw={'readonly': True})
    submit = SubmitField(label='Released')


# Payment Form
# Validates input for processing payments.

class PaymentForm(FlaskForm):
    """Form for processing payments with amount and payment method selection."""

    amount = FloatField('Amount', validators=[DataRequired()])
    payment_method = SelectField(
        'Payment Method',
        choices=[
            ('upi', 'UPI'),
            ('card', 'Credit/Debit Card'),
            ('netbanking', 'Net Banking'),
            ('wallet', 'Mobile Wallet'),
            ('paypal', 'PayPal'),
            ('crypto', 'Cryptocurrency'),
            ('bank_transfer', 'Direct Bank Transfer'),
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField('Make Payment')


# Parking Spot Deletion Form
# Validates input for deleting a parking spot.

class DeleteParkingSpotForm(FlaskForm):
    """Form for deleting a parking spot with hidden spot ID."""

    spot_id = HiddenField(validators=[DataRequired()])
    submit = SubmitField('Delete Spot')


# User Profile Form
# Validates input for updating user profile information.

class ProfileForm(FlaskForm):
    """Form for updating user profile details including bio and profile picture."""

    full_name = StringField('Full Name', validators=[DataRequired()])
    bio = TextAreaField('Bio')
    date_of_birth = DateField(
        'Date of Birth',
        format='%Y-%m-%d',
        validators=[DataRequired()]
    )
    profile_pic = FileField('Profile Picture')
    save_changes = SubmitField('Save Changes')
    delete_profile = SubmitField('Delete Profile')


# CSRF Protection Form
# Provides CSRF token for forms without additional fields.

class CsrfOnlyForms(FlaskForm):
    """Form for CSRF protection in templates without additional input fields."""

    pass

# End of Forms Module