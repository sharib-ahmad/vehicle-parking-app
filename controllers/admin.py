
from functools import wraps
from flask import (Blueprint, Response, current_app, flash, redirect,
                   render_template, request, session, url_for)
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError

from models import (ParkingLot, CsrfOnlyForms
, ParkingLotForm,EditParkingLotForm, ParkingSpot, SpotStatus, db)









admin_bp = Blueprint('admin', __name__)




def admin_required(f):
    """ Restricts access to admin users only. """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('You do not have permission to access this page.', 'danger')
            current_app.logger.warning(
                f'Unauthorized admin access attempt by user {current_user.id} ({current_user.email})')
            return redirect(url_for('local.index'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/parking-lots')
@admin_required
def parking_lots():
    """ Displays all parking lots. """
    parking_lots = ParkingLot.query.all()
    form = CsrfOnlyForms()
    return render_template('admin/parking_lots.html', parking_lots=parking_lots, form=form)


@admin_bp.route('/parking-lot/add', methods=['GET', 'POST'])
@admin_required
def add_parking_lot():
    """ Handles the creation of a new parking lot. """
    form = ParkingLotForm()
    if form.validate_on_submit():
        try:
            # --- Create a new parking lot ---
            new_lot = ParkingLot(
                name=form.name.data,
                prime_location_name=form.prime_location_name.data,
                price_per_hour=form.price_per_hour.data,
                address=form.address.data,
                pin_code=form.pin_code.data,
                floor_level=form.floor_level.data,
                maximum_number_of_spots=form.maximum_number_of_spots.data,
                open_time=form.open_time.data,
                close_time=form.close_time.data
            )
            db.session.add(new_lot)
            db.session.flush()

            # --- Create parking spots for the new lot ---
            for i in range(1, form.maximum_number_of_spots.data + 1):
                spot = ParkingSpot(
                    spot_number=f"{new_lot.id}-{i}",
                    lot_id=new_lot.id,
                    status=SpotStatus.AVAILABLE,
                )
                db.session.add(spot)
            db.session.commit()

            flash(f'Parking lot "{form.name.data}" created successfully.', 'success')
            current_app.logger.info(
                f'Parking lot "{form.name.data}" created successfully by admin {current_user.id}')
            return redirect(url_for('admin.parking_lots'))

        except SQLAlchemyError as e:
            db.session.rollback()
            flash("An error occurred while saving to the database.", "danger")
            current_app.logger.error(f'Database error (add lot): {str(e)}')
            return redirect(url_for('admin.add_parking_lot'))

        finally:
            db.session.close()

    # --- Flash form errors ---
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error in {field}: {error}', 'danger')
                current_app.logger.warning(f'Form error in {field}: {error}')

    return render_template('admin/add_parking_lot.html', form=form)



@admin_bp.route('/parking-lot/<int:lot_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_parking_lot(lot_id):
    """Handles editing an existing parking lot."""
    parking_lot = ParkingLot.query.get_or_404(lot_id)
    form = EditParkingLotForm(obj=parking_lot)
    form.floor_level.choices = [(parking_lot.floor_level, parking_lot.floor_level)]

    if form.validate_on_submit():
        try:
            parking_lot.price_per_hour = form.price_per_hour.data
            parking_lot.open_time = form.open_time.data
            parking_lot.close_time = form.close_time.data
            parking_lot.is_active = form.is_active.data == 'true'
            db.session.commit()

            flash(f'Parking lot "{parking_lot.name}" updated successfully.', 'success')
            current_app.logger.info(f'Parking lot "{parking_lot.name}" updated by admin {current_user.id}')
            return redirect(url_for('admin.parking_lots'))

        except SQLAlchemyError as e:
            db.session.rollback()
            flash("An error occurred while saving to the database.", "danger")
            current_app.logger.error(f'Database error (edit lot): {str(e)}')
            return redirect(url_for('admin.edit_parking_lot', lot_id=lot_id))

        finally:
            db.session.close()

    return render_template('admin/edit_parking_lot.html', form=form, parking_lot=parking_lot)

@admin_bp.route('/parking-lot/<int:lot_id>/delete', methods=['POST'])
@admin_required
def delete_parking_lot(lot_id):
    """Handles deleting a parking lot."""
    lot = ParkingLot.query.get_or_404(lot_id)

    if lot.occupied_spots > 0:
        flash('Cannot delete a parking lot with occupied spots.', 'danger')
        current_app.logger.warning(f'Attempt to delete occupied lot "{lot.name}" by admin {current_user.id}')
        return redirect(url_for('admin.parking_lots'))

    try:
        db.session.delete(lot)
        db.session.commit()

        flash(f'Parking lot "{lot.name}" and all related spots have been deleted.', 'success')
        current_app.logger.info(
            f'Parking lot "{lot.name}" and all related spots deleted by admin {current_user.id}')
        return redirect(url_for('admin.parking_lots'))

    except SQLAlchemyError as e:
        db.session.rollback()
        flash("An error occurred while saving to the database.", "danger")
        current_app.logger.error(f'Database error (delete lot): {str(e)}')
        return redirect(url_for('admin.delete_parking_lot', lot_id=lot_id))

    finally:
        db.session.close()