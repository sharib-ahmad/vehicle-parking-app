from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField, FloatField, BooleanField, TextAreaField, TimeField, DateTimeField, HiddenField, DateField, FileField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange
from models import User


class RegistrationForm(FlaskForm):
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email.')
        
    def validate_phone_number(self, phone_number):
        user = User.query.filter_by(phone_number=phone_number.data).first()
        if user:
            raise ValidationError('Phone number already registered. Please use a different phone number.')

    full_name = StringField(label='Full Name', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField(label='Email', filters=[lambda x: x.strip() if x else x], validators=[DataRequired(), Email()])
    password_hash = PasswordField(label='Password', validators=[DataRequired()])
    confirm_password = PasswordField(label='Confirm Password', validators=[DataRequired(), EqualTo('password_hash')])
    phone_number = StringField(label='Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    address = StringField(label='Address', validators=[DataRequired()])
    pin_code = StringField(label='Pin Code', validators=[DataRequired(), Length(min=6, max=10)])
    submit = SubmitField(label='Register')

class LoginForm(FlaskForm):
    email = StringField(label='Registered Email Id', validators=[DataRequired(), Email()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    submit = SubmitField(label='Login')


class ParkingLotForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    prime_location_name = StringField(label='Prime Location Name', validators=[DataRequired()])
    price_per_hour = FloatField(label='Price per Hour', validators=[DataRequired(), NumberRange(min=0)])
    address = TextAreaField(label='Address', validators=[DataRequired()])
    pin_code = StringField(label='Pin Code', validators=[DataRequired()])
    floor_level = SelectField(label='Floor Level', choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')], validators=[DataRequired()])
    maximum_number_of_spots = IntegerField(label='Maximum Number of Spots', validators=[DataRequired(), NumberRange(min=1)])
    open_time = TimeField(label='Open Time', format='%H:%M')
    close_time = TimeField(label='Close Time', format='%H:%M')
    submit = SubmitField(label='Add Lot')

class EditParkingLotForm(FlaskForm):
    name = StringField(label='Name', validators=[DataRequired()], render_kw={'readonly': True})
    prime_location_name = StringField(label='Prime Location', validators=[DataRequired()], render_kw={'readonly': True})
    price_per_hour = FloatField(label='Price per Hour', validators=[DataRequired(), NumberRange(min=0)])
    address = StringField(label='Address', validators=[DataRequired()], render_kw={'readonly': True})
    pin_code = StringField(label='Pin Code', validators=[DataRequired()], render_kw={'readonly': True})
    floor_level = SelectField(label='Floor Level', choices=[], validators=[DataRequired()],render_kw={'readonly':True})
    open_time = TimeField(label='Open Time', format='%H:%M')
    close_time = TimeField(label='Close Time', format='%H:%M')
    is_active = SelectField(
        label='Active',
        validators=[DataRequired()],
        choices=[('true', 'True'), ('false', 'False')]) 
    maximum_number_of_spots = IntegerField(label='Max Number of Spots', validators=[DataRequired(), NumberRange(min=1)],render_kw={'readonly' : True})
    submit = SubmitField(label='Update')

class UserSearchForm(FlaskForm):
    location = StringField(label='Search by Location', validators=[DataRequired()])
    submit = SubmitField(label='Search')

class CsrfOnlyForms(FlaskForm):
    pass