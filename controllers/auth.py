from flask import Blueprint, render_template,redirect , url_for, flash, current_app
from flask_login import login_user
from models import db, User, RegistrationForm
from sqlalchemy.exc import SQLAlchemyError
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

















