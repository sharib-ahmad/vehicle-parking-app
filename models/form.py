from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
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


class CsrfOnlyForms(FlaskForm):
    pass