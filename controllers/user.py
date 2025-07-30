"""
# User Controller
# This module manages user-related functionality, including dashboard display, parking reservations,
# payment processing, profile management, and analytics visualizations.
"""

import io
import os
import random
from datetime import datetime

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import requests
from flask import (Blueprint, Response, current_app, flash, redirect,
                    render_template, request, session, url_for, send_file, abort)
from flask_login import current_user, login_required, logout_user
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError

from models.forms import (UserSearchForm, ReservedSpotForm, ReleasedForm,
                        PaymentForm, ProfileForm)

from models.model import (IST, ParkingLot, ReservationStatus, PaymentStatus,Payment,UserProfile,
                        ParkingSpot, ReservedParkingSpot, SpotStatus, User,
                        Vehicle, db)

matplotlib.use("Agg")

user_bp = Blueprint("user", __name__)

# Dashboard and Search Functionality
# Handles user dashboard rendering and parking lot searches.


@user_bp.route("/dashboard", methods=["GET", "POST"])
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
    now = datetime.now(IST).time()
    search_location = session.get("search_location", "")

    if form.validate_on_submit():
        search_location = form.location.data.strip()
        session["search_location"] = search_location
        return redirect(url_for("user.dashboard"))

    # Search logic
    if search_location:
        lots = ParkingLot.query.filter(
            or_(
                ParkingLot.prime_location_name.ilike(f"%{search_location}%"),
                ParkingLot.pin_code.ilike(f"%{search_location}%"),
                ParkingLot.prime_location_name.ilike(f"%{search_location}%"),
                ParkingLot.city.ilike(f"%{search_location}%"),
                ParkingLot.state.ilike(f"%{search_location}%"),
                ParkingLot.district.ilike(f"%{search_location}%")
            )
        ).all()
    else:
        

        # Fetch lots that are active and currently open
        lots = ParkingLot.query.filter(
            ParkingLot.is_active == True,
            ParkingLot.open_time <= now,
            ParkingLot.close_time >= now,
        ).all()

    # Get user reservations
    reservations = (
        ReservedParkingSpot.query.filter_by(user_id=current_user.id)
        .order_by(ReservedParkingSpot.reservation_timestamp.desc())
        .all()
    )

    form.location.data = search_location

    return render_template(
        "user/dashboard.html",
        form=form,
        parking_lots=lots,
        search_location=search_location,
        reservations=reservations,
        current_time=now,
    )


@user_bp.route("/clear-search")
@login_required
def clear_search():
    """
    Clears the search session from the dashboard.
    - Removes search location from session
    - Redirects back to dashboard with all lots visible
    """
    session.pop("search_location", None)
    flash("Search cleared.", "info")
    current_app.logger.info(f"User {current_user.id} cleared dashboard search")

    return redirect(url_for("user.dashboard"))


# Reservation Management
# Manages the reservation process for parking spots.


@user_bp.route("/reserve-spot/<int:lot_id>", methods=["GET", "POST"])
@login_required
def reserve_spot(lot_id):
    """
    Handles the process of reserving a parking spot.
    Features:
    - Automatically finds available spots
    - Fetches vehicle data from external APIs
    - Creates reservation and updates vehicle info
    - Prevents duplicate reservations for the same vehicle
    """
    lot = ParkingLot.query.get_or_404(lot_id)
    form = ReservedSpotForm()

    # Find an available spot
    available_spots = [
        spot.id for spot in lot.parking_spots if spot.status == SpotStatus.AVAILABLE
    ]
    if not available_spots:
        flash("No available spots in this lot.", "danger")
        current_app.logger.warning(
            f"User {current_user.id} tried to reserve in full lot {lot_id}"
        )
        return redirect(url_for("user.dashboard"))

    preselected_spot_id = random.choice(available_spots)

    # Populate form choices from external APIs
    try:
        df = pd.read_csv("Cars.csv", encoding='ISO-8859-1')

        df = df.dropna(subset=['Company Names', 'Cars Names'])

        df['Company Names'] = df['Company Names'].str.strip().str.capitalize()
        df['Cars Names'] = df['Cars Names'].str.strip().str.capitalize()

        brands = sorted(df['Company Names'].unique())
        models = sorted(df['Cars Names'].unique())
        form.brand.choices = [(b, b) for b in brands]
        form.model.choices = [(m, m) for m in models]

    except FileNotFoundError:
        current_app.logger.error("Cars.csv not found")
        flash("Could not load vehicle data. Please try again later.", "danger")
        return redirect(url_for("user.dashboard"))
    
    try:
        color_df = pd.read_csv("colors.csv", encoding='utf-8')
        color_df = color_df.dropna(subset=["name"])
        
        # Ensure name column is stripped and capitalized properly
        color_df["name"] = color_df["name"].str.strip()

        # Create color choices: (value, label)
        form.color.choices = [(row["key"], row["name"]) for _, row in color_df.iterrows()]
    except FileNotFoundError:
        current_app.logger.error("colors.csv not found")
        flash("Could not load vehicle colors. Please try again later.", "danger")




    if request.method == "GET":
        now = datetime.now(IST).time()
        if not (lot.open_time <= now <= lot.close_time):
            flash(
                f"The parking lot is currently closed. Please try again between {lot.open_time} and {lot.close_time}.",
                "danger",
            )
            current_app.logger.warning(
                f"User {current_user.id} tried to reserve outside of lot hours {lot_id}"
            )
            return redirect(url_for("user.dashboard"))

        form.lot_id.data = lot_id
        form.user_id.data = current_user.id
        form.spot_id.data = preselected_spot_id

    if form.validate_on_submit():
        # Check for existing active reservations for the same vehicle
        if ReservedParkingSpot.query.filter_by(
            vehicle_number=form.vehicle_number.data, leaving_timestamp=None
        ).first():
            flash(
                f"You already have an active reservation for vehicle {form.vehicle_number.data}.",
                "danger",
            )
            return redirect(url_for("user.dashboard"))

        # Insert new vehicle if it doesn't exist
        if not Vehicle.query.filter_by(vehicle_number=form.vehicle_number.data).first():
            new_vehicle = Vehicle(
                user_id=form.user_id.data,
                vehicle_number=(form.vehicle_number.data).strip(),
                fuel_type=form.fuel_type.data,
                brand=form.brand.data,
                model=form.model.data,
                color=form.color.data,
            )
            db.session.add(new_vehicle)
            db.session.flush()

        reservation = ReservedParkingSpot(
            spot_id=form.spot_id.data,
            user_id=form.user_id.data,
            parking_cost_per_hour=lot.price_per_hour,
            vehicle_number=form.vehicle_number.data,
            parking_timestamp=datetime.now(IST),
        )
        db.session.add(reservation)

        spot = ParkingSpot.query.get_or_404(form.spot_id.data)
        spot.status = SpotStatus.OCCUPIED
        spot.is_covered = True
        db.session.add(spot)

        try:
            db.session.commit()
            flash(
                f"Parking spot #{reservation.parking_spot.spot_number} reserved successfully.",
                "success",
            )
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Reservation failed: {str(e)}")
            flash(
                "Something went wrong while reserving the spot. Please try again.",
                "danger",
            )

        return redirect(url_for("user.dashboard"))

    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {field}: {error}", "danger")

    return render_template("user/reserve_spot.html", form=form, lot=lot)


# Payment and Vehicle Release
# Manages the release of vehicles and payment processing.


@user_bp.route("/reservation/<int:reservation_id>/released", methods=["GET", "POST"])
@login_required
def released(reservation_id):
    """
    Handles the release of a vehicle and calculates cost.
    Features:
    - Calculates parking duration and total cost
    - Handles timezone-aware timestamp calculations
    - Stores temporary data in session for payment process
    - Redirects to payment gateway
    """
    reservation = ReservedParkingSpot.query.get_or_404(reservation_id)
    form = ReleasedForm(obj=reservation)

    leaving_timestamp = datetime.now(IST)
    aware_parking_timestamp = (
        reservation.parking_timestamp.replace(tzinfo=IST)
        if reservation.parking_timestamp.tzinfo is None
        else reservation.parking_timestamp
    )

    duration_seconds = (leaving_timestamp - aware_parking_timestamp).total_seconds()
    duration_hours = round(duration_seconds / 3600, 2)
    total_cost = round(duration_hours * reservation.parking_cost_per_hour, 2)

    form.leaving_timestamp.data = leaving_timestamp
    form.duration.data = str(duration_hours)
    form.total_cost.data = f"{total_cost} Rs"

    if form.validate_on_submit():
        # Store temporary data in session before payment
        session["temp_leaving_timestamp"] = leaving_timestamp.isoformat()
        session["temp_duration"] = duration_hours
        session["temp_total_cost"] = total_cost

        flash("Please complete the payment for the vehicle to be released.", "info")
        return redirect(url_for("user.make_payment", reservation_id=reservation.id))

    return render_template("user/released.html", form=form, reservation=reservation)


@user_bp.route("/reservation/<int:reservation_id>/payment", methods=["GET", "POST"])
@login_required
def make_payment(reservation_id):
    """
    Handles the payment process for a reservation.
    Features:
    - Processes payment and updates reservation status
    - Updates parking spot availability
    - Records payment transaction
    - Updates parking lot revenue
    - Clears temporary session data
    """
    reservation = ReservedParkingSpot.query.get_or_404(reservation_id)

    try:
        leaving_timestamp = datetime.fromisoformat(session["temp_leaving_timestamp"])
        duration = session["temp_duration"]
        total_cost = session["temp_total_cost"]
    except KeyError:
        flash("Session expired. Please release the vehicle again.", "danger")
        return redirect(url_for("user.dashboard"))

    form = PaymentForm()
    form.amount.data = total_cost

    if form.validate_on_submit():
        reservation.leaving_timestamp = leaving_timestamp
        reservation.status = ReservationStatus.COMPLETED
        reservation.parking_spot.is_covered = False
        reservation.parking_spot.status = SpotStatus.AVAILABLE
        reservation.parking_spot.revenue += total_cost

        payment = Payment(
            reservation_id=reservation.id,
            amount=form.amount.data,
            payment_method=form.payment_method.data,
            payment_status="PAID",
        )

        lot = ParkingLot.query.get(reservation.parking_spot.lot_id)
        lot.revenue += total_cost

        db.session.add_all([reservation, payment, lot])
        db.session.commit()

        # Clear temporary session data
        session.pop("temp_leaving_timestamp", None)
        session.pop("temp_duration", None)
        session.pop("temp_total_cost", None)

        flash("Payment successful!", "success")
        return redirect(url_for("user.dashboard"))

    return render_template(
        "user/payment.html", form=form, reservation=reservation, total_cost=total_cost
    )


@user_bp.route("/payment/cancel")
@login_required
def cancel_payment():
    """
    Cancels the payment process.
    - Clears all temporary session data
    - Redirects user back to dashboard
    - No changes are saved to database
    """
    session.pop("temp_leaving_timestamp", None)
    session.pop("temp_duration", None)
    session.pop("temp_total_cost", None)
    flash("Payment cancelled. No changes were saved.", "info")
    return redirect(url_for("user.dashboard"))


# User Profile Management
# Manages user profile updates and deletion requests.


@user_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """
    Manages user profile updates and deletion requests.
    Features:
    - Updates user profile information
    - Handles profile picture uploads
    - Manages account deletion scheduling
    - Form validation and error handling
    """
    form = ProfileForm(obj=current_user.profile)

    if form.validate_on_submit():
        current_user.full_name = form.full_name.data
        if current_user.profile is None:
            current_user.profile = UserProfile()

        current_user.profile.bio = form.bio.data
        current_user.profile.date_of_birth = form.date_of_birth.data

        if form.profile_pic.data:
            current_user.profile.image = form.profile_pic.data.read()
            current_user.profile.image_mimetype = form.profile_pic.data.mimetype

        if form.save_changes.data:
            db.session.commit()
            flash("Profile updated successfully.", "success")
            current_app.logger.info(f"User {current_user.id} updated profile")
        elif form.delete_profile.data:
            current_user.schedule_deletion()
            user_id = current_user.id
            db.session.commit()
            logout_user()
            flash("Your profile is scheduled to be deleted in 15 days.", "warning")
            current_app.logger.info(f"User {user_id} scheduled profile deletion")
            return redirect(url_for("auth.login"))

        return redirect(url_for("user.profile"))

    form.full_name.data = current_user.full_name
    return render_template("user/profile.html", form=form, user=current_user)

@user_bp.route("/profile-image/<string:user_id>")
@login_required
def profile_image(user_id):
    user_profile = UserProfile.query.filter_by(user_id=user_id).first()
    if user_profile and user_profile.image:
        return send_file(io.BytesIO(user_profile.image), mimetype=user_profile.image_mimetype)
    else:
        return abort(404)
# Background Tasks
# Handles background tasks such as deleting scheduled users.


def delete_scheduled_users():
    """
    Deletes users who have been scheduled for deletion.
    Features:
    - Finds users scheduled for deletion after expiry date
    - Permanently removes user accounts from database
    - Runs as background/scheduled task
    """
    now = datetime.now()
    users_to_delete = User.query.filter(
        User.is_active == False,
        User.scheduled_delete_at != None,
        User.scheduled_delete_at <= now,
    ).all()

    for user in users_to_delete:
        db.session.delete(user)

    db.session.commit()


# Analytics and Visualizations
# Generates user-specific analytics and visualizations.


@user_bp.route("/summary")
@login_required
def summary():
    """
    Renders the user summary page with reservation and payment info.
    - Shows parking history
    - Displays amount spent per reservation
    """
    reservations = (
        ReservedParkingSpot.query.filter_by(user_id=current_user.id)
        .order_by(ReservedParkingSpot.reservation_timestamp.desc())
        .all()
    )

    total_spent = sum(
        r.payment.amount
        for r in reservations
        if r.payment and r.payment.payment_status == PaymentStatus.PAID
    )

    return render_template(
        "user/summary.html",
        reservations=reservations,
        total_spent=round(total_spent, 2) or 0.0,
    )


@user_bp.route("/chart/parking-spot-summary")
@login_required
def parking_spot_summary_chart():
    """
    Generates a bar chart of amounts invested per parking spot.
    Handles missing/deleted spots gracefully.
    """
    reservations = ReservedParkingSpot.query.filter_by(user_id=current_user.id).all()
    spot_labels, amounts = [], []

    for r in reservations:
        if r.payment and r.payment.payment_status == PaymentStatus.PAID:
            if r.parking_spot:
                label = f"Spot({r.parking_spot.spot_number})"
            else:
                label = "Deleted Spot"
            spot_labels.append(label)
            amounts.append(r.payment.amount)

    if not spot_labels:
        spot_labels, amounts = ["No Data"], [0]

    # Create chart
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(
        spot_labels, amounts, color=["#4CAF50", "#2196F3", "#f44336", "#FFC107"]
    )

    ax.set_title("Amount Invested by You per Parking Spot")
    ax.set_xlabel("Spot")
    ax.set_ylabel("Amount (₹)")
    ax.yaxis.grid(True, linestyle="--", alpha=0.6)

    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + 1,
            f"₹{amounts[i]:.2f}",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    ax.set_ylim(0, max(amounts) + 100 if amounts else 100)
    fig.tight_layout()

    # Return image response
    img_io = io.BytesIO()
    FigureCanvas(fig).print_png(img_io)
    img_io.seek(0)
    plt.close(fig)

    return Response(img_io.getvalue(), mimetype="image/png")


@user_bp.route("/download/parking-spot-summary")
@login_required
def download_parking_spot_summary():
    """
    Returns a detailed Excel summary of user's parking history.
    """
    reservations = ReservedParkingSpot.query.filter_by(user_id=current_user.id).all()
    data = []
    total_spent = 0

    for r in reservations:
        if r.payment and r.payment.payment_status == PaymentStatus.PAID:
            spot = (
                f"Spot({r.parking_spot.spot_number})"
                if r.parking_spot
                else "Deleted Spot"
            )
            vehicle = r.vehicle_number or "N/A"

            start_time = (
                r.parking_timestamp.strftime("%Y-%m-%d %H:%M")
                if r.parking_timestamp
                else "N/A"
            )
            end_time = (
                r.leaving_timestamp.strftime("%Y-%m-%d %H:%M")
                if r.leaving_timestamp
                else "N/A"
            )

            # Calculate duration
            if r.parking_timestamp and r.leaving_timestamp:
                duration = r.leaving_timestamp - r.parking_timestamp
                duration_str = str(duration)
            else:
                duration_str = "N/A"

            amount = r.payment.amount
            total_spent += amount

            payment_time = (
                r.payment.payment_timestamp.strftime("%Y-%m-%d %H:%M")
                if r.payment.payment_timestamp
                else "N/A"
            )

            data.append(
                {
                    "Parking Spot": spot,
                    "Vehicle Number": vehicle,
                    "Parking Time": start_time,
                    "Leaving Time": end_time,
                    "Duration": duration_str,
                    "Amount Paid (₹)": amount,
                    "Payment Time": payment_time,
                }
            )

    if not data:
        data = [
            {
                "Parking Spot": "No Data",
                "Vehicle Number": "N/A",
                "Paking Time": "N/A",
                "Leaving Time": "N/A",
                "Duration": "N/A",
                "Amount Paid (₹)": 0,
                "Payment Time": "N/A",
            }
        ]

    df = pd.DataFrame(data)

    # Add total at the end
    df.loc[len(df.index)] = ["", "", "", "", "Total", total_spent, ""]

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Parking Summary")

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment;filename=parking_summary_detailed.xlsx"
        },
    )


# End of User Controller
