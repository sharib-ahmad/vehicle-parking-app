"""
# Authentication Controller
# This module manages user authentication, including registration, login, and logout functionality.
# It handles form validation, database operations, and user session management.
"""

import random
from datetime import datetime

from flask import Blueprint, current_app, flash, redirect, render_template, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy.exc import SQLAlchemyError

from models import LoginForm, RegistrationForm, User, db

auth_bp = Blueprint('auth', __name__)

# User Registration
# Handles the creation of new user accounts.

@auth_bp.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    """
    Handles user registration.
    - Creates a new user account with a unique ID
    - Validates form data and manages database operations
    - Automatically logs in the user after successful registration
    """
    form = RegistrationForm()
    
    if form.validate_on_submit():
        try:
            # Create a new user with a unique ID
            user = User(
                id='@' + form.email.data.split('@')[0] + str(random.randint(100, 999)),
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

            flash(f'Account created successfully! You are logged in as {user.full_name}', 'success')
            current_app.logger.info(f"User account with user_email <{user.email}> registered successfully.")
            
            return redirect(url_for('user.dashboard'))

        except SQLAlchemyError as e:
            db.session.rollback()
            flash("An error occurred while saving to the database.", "danger")
            current_app.logger.error(f"Database error during registration: {str(e)}")
            
            return redirect(url_for('auth.sign_up'))

        finally:
            db.session.close()

    # Flash form errors
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error in {field}: {error}', 'danger')

    return render_template('auth/registration.html', form=form)

# User Login
# Manages user login and account recovery for soft-deleted accounts.

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles user login.
    - Validates user credentials
    - Manages recovery of soft-deleted accounts
    - Redirects based on user role (admin or user)
    """
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip()).first()

        if user and user.check_password(form.password.data):
            
            # Check if the user account is soft-deleted
            if not user.is_active and user.scheduled_delete_at:
                now = datetime.now(user.created_at.tzinfo)
                
                if now < user.scheduled_delete_at:
                    # Cancel deletion if the user logs in before the scheduled deletion date
                    user.cancel_deletion()
                    db.session.commit()
                    flash("Welcome back! Your account deletion was canceled.", "success")
                    current_app.logger.info(f'Welcome back! {current_user.id} Your account deletion was canceled.')
                    
                else:
                    # If deletion time has passed
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

            # Redirect based on user role
            if current_user.is_admin():
                return redirect(url_for('admin.parking_lots'))
            else:
                return redirect(url_for('user.dashboard'))
                
        else:
            flash("Invalid email or password", "danger")
            current_app.logger.error('Invalid email or password')

    return render_template('auth/login.html', form=form)

# User Logout
# Manages user logout and session termination.

@auth_bp.route('/logout')
def logout():
    """
    Handles user logout.
    - Safely logs out the current user
    - Logs the logout event
    - Redirects to the home page
    """
    user_logout = current_user.id
    logout_user()
    
    flash('You have been logged out.', 'success')
    current_app.logger.info(f'User <{user_logout}> has been logged out.')
    
    return redirect(url_for('local.index'))

# End of Authentication Controller