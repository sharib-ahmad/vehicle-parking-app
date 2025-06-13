
import os
from flask import (Blueprint, Response, current_app, flash, redirect,
                   render_template, request, session, url_for)
from flask_login import current_user, login_required
from sqlalchemy import or_
from models import (ParkingLot, ReservedParkingSpot,UserSearchForm,db)

















user_bp = Blueprint('user', __name__)

# Dashboard and Search Functionality
# Handles user dashboard rendering and parking lot searches.

@user_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    """
    Renders the user dashboard and handles parking lot searches.
    Features:
    - Search parking lots by location, name, or pin code
    - Display available parking lots
    - Show user's reservation history
    - Maintain session-based search persistence
    """
    form = UserSearchForm()
    lots = []
    search_location = session.get("search_location", "")

    if form.validate_on_submit():
        search_location = form.location.data.strip()
        session["search_location"] = search_location
        return redirect(url_for("user.dashboard"))

    # Search logic
    if search_location:
        lots = ParkingLot.query.filter(
            or_(
                ParkingLot.name.ilike(f"%{search_location}%"),
                ParkingLot.pin_code.ilike(f"%{search_location}%"),
                ParkingLot.prime_location_name.ilike(f"%{search_location}%")
            )
        ).all()
    else:
        lots = ParkingLot.query.all()

    # Get user reservations
    reservations = ReservedParkingSpot.query.filter_by(user_id=current_user.id).order_by(
        ReservedParkingSpot.reservation_timestamp.desc()).all()

    form.location.data = search_location
    
    return render_template('user/dashboard.html', 
                         form=form, 
                         parking_lots=lots, 
                         search_location=search_location, 
                         reservations=reservations)


@user_bp.route('/clear-search')
@login_required
def clear_search():
    """
    Clears the search session from the dashboard.
    - Removes search location from session
    - Redirects back to dashboard with all lots visible
    """
    session.pop('search_location', None)
    flash('Search cleared.', 'info')
    current_app.logger.info(f'User {current_user.id} cleared dashboard search')
    
    return redirect(url_for('user.dashboard'))