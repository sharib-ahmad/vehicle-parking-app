from flask import Blueprint, render_template,redirect , url_for, flash, current_app
from flask_login import login_user, current_user
from models import db, User, UserRole, RegistrationForm, LoginForm
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import random



auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(
                id = '@' + form.email.data.split('@')[0] + str(random.randint(100,999)),
                full_name=form.full_name.data,
                email=(form.email.data).strip(),
                password=(form.password_hash.data).strip(),
                phone_number=form.phone_number.data,
                address=form.address.data,
                pin_code=form.pin_code.data
            )
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash(f'Account created succesfully! You are loged in as {user.full_name}', 'success')
            current_app.logger.info(f"User account with user_email <{user.email}> registered successfully.")
            return redirect(url_for('user.dashboard'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash("An error occurred while saving to the database.", "danger")
            current_app.logger.error(f"Database error during registration: {str(e)}")
            return redirect(url_for('auth.sign_up'))
        finally:
            db.session.close()

    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error in {field}: {error}', 'danger')
    return render_template('auth/registration.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip()).first()

        if user and user.check_password(form.password.data):
            # Check if user account is soft-deleted
            if not user.is_active and user.scheduled_delete_at:
                now = datetime.now(user.created_at.tzinfo)
                if now < user.scheduled_delete_at:
                    # Cancel deletion
                    user.cancel_deletion()
                    db.session.commit()
                    flash("Welcome back! Your account deletion was canceled.", "success")
                    current_app.logger.info(f'Welcome back! {current_user.id} Your account deletion was canceled.')
                else:
                    # Deletion time passed
                    flash("Your account has already been permanently deleted.", "danger")
                    current_app.logger.info('Your account has already been permanently deleted.')
                    return redirect(url_for('auth.login'))

            elif not user.is_active:
                flash("Your account is inactive. Please contact support.", "danger")
                current_app.logger.info(f'Your account is inactive. Please contact support.{user.id}')
                return redirect(url_for('auth.login'))

            # Login the user
            login_user(user)
            flash("Login successful!", "success")
            current_app.logger.info(f'Login successful! {current_user.id}')
            if current_user.role == UserRole.USER:
                return redirect(url_for('user.dashboard'))
            else:
                return redirect(url_for('admin.parking_lots'))
        else:
            flash("Invalid email or password", "danger")
            current_app.logger.error(f'Invalid email or password')

    return render_template('auth/login.html', form=form)














