"""
# Admin Control Panel
# This module handles administrative functions for managing parking lots, users, and spots.
# It includes routes for creating, editing, and deleting parking lots and spots,
# as well as searching and generating summary charts.
"""

import io
from datetime import datetime
from functools import wraps

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from flask import (Blueprint, Response, current_app, flash, redirect,
                   render_template, request, session, url_for)
from flask_login import current_user, login_required
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError

from models.forms import (AdminSearchForm, CsrfOnlyForms, DeleteParkingSpotForm,
                    EditParkingLotForm, ParkingLotForm)

from models.model import (IST, ParkingLot,ParkingSpot, ReservedParkingSpot, SpotStatus, User,
                    UserRole, Vehicle, db)

matplotlib.use("Agg")

# Blueprint Initialization
# Sets up the admin blueprint for routing.

admin_bp = Blueprint("admin", __name__)

# Decorators
# Defines custom decorators for restricting access to admin users.


def admin_required(f):
    """Restricts access to admin users only."""

    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash("You do not have permission to access this page.", "danger")
            current_app.logger.warning(
                f"Unauthorized admin access attempt by user {current_user.id} ({current_user.email})"
            )
            return redirect(url_for("local.index"))
        return f(*args, **kwargs)

    return decorated_function


# Parking Lot Management
# Handles creation, editing, and deletion of parking lots.


@admin_bp.route("/parking-lots")
@admin_required
def parking_lots():
    """Displays all parking lots."""
    parking_lots = ParkingLot.query.all()
    form = CsrfOnlyForms()
    return render_template(
        "admin/parking_lots.html", parking_lots=parking_lots, form=form
    )


@admin_bp.route("/parking-lot/add", methods=["GET", "POST"])
@admin_required
def add_parking_lot():
    """Handles the creation of a new parking lot."""
    form = ParkingLotForm()
    if form.validate_on_submit():
        try:
            # Create a new parking lot
            new_lot = ParkingLot(
                prime_location_name=form.prime_location_name.data,
                pin_code=form.pin_code.data,
                city=form.city.data,
                state=form.state.data,
                district=form.district.data,
                address=f'{form.prime_location_name.data}, {form.city.data}, {form.district.data}, {form.pin_code.data}, {form.state.data}',
                price_per_hour=form.price_per_hour.data,
                floor_level=form.floor_level.data,
                maximum_number_of_spots=form.maximum_number_of_spots.data,
                open_time=form.open_time.data,
                close_time=form.close_time.data,
            )
            db.session.add(new_lot)
            db.session.flush()

            # Create parking spots for the new lot
            for i in range(1, form.maximum_number_of_spots.data + 1):
                spot = ParkingSpot(
                    spot_number=f"{new_lot.id}-{i}",
                    lot_id=new_lot.id,
                    status=SpotStatus.AVAILABLE,
                )
                db.session.add(spot)
            db.session.commit()

            flash(f'Parking lot "{form.prime_location_name.data}" created successfully.', "success")
            current_app.logger.info(
                f'Parking lot "{form.prime_location_name.data}" created successfully by admin {current_user.id}'
            )
            return redirect(url_for("admin.parking_lots"))

        except SQLAlchemyError as e:
            db.session.rollback()
            flash("An error occurred while saving to the database.", "danger")
            current_app.logger.error(f"Database error (add lot): {str(e)}")
            return redirect(url_for("admin.add_parking_lot"))

        finally:
            db.session.close()

    # Flash form errors
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {field}: {error}", "danger")
                current_app.logger.warning(f"Form error in {field}: {error}")

    return render_template("admin/add_parking_lot.html", form=form)


@admin_bp.route("/parking-lot/<int:lot_id>/edit", methods=["GET", "POST"])
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
            parking_lot.is_active = form.is_active.data == "true"
            db.session.commit()

            flash(f'Parking lot "{parking_lot.prime_location_name}" updated successfully.', "success")
            current_app.logger.info(
                f'Parking lot "{parking_lot.prime_location_name}" updated by admin {current_user.id}'
            )
            return redirect(url_for("admin.parking_lots"))

        except SQLAlchemyError as e:
            db.session.rollback()
            flash("An error occurred while saving to the database.", "danger")
            current_app.logger.error(f"Database error (edit lot): {str(e)}")
            return redirect(url_for("admin.edit_parking_lot", lot_id=lot_id))

        finally:
            db.session.close()

    return render_template(
        "admin/edit_parking_lot.html", form=form, parking_lot=parking_lot
    )


@admin_bp.route("/parking-lot/<int:lot_id>/delete", methods=["POST"])
@admin_required
def delete_parking_lot(lot_id):
    """Handles deleting a parking lot."""
    lot = ParkingLot.query.get_or_404(lot_id)

    if lot.occupied_spots > 0:
        flash("Cannot delete a parking lot with occupied spots.", "danger")
        current_app.logger.warning(
            f'Attempt to delete occupied lot "{lot.prime_location_name}" by admin {current_user.id}'
        )
        return redirect(url_for("admin.parking_lots"))

    try:
        db.session.delete(lot)
        db.session.commit()

        flash(
            f'Parking lot "{lot.prime_location_name}" and all related spots have been deleted.',
            "success",
        )
        current_app.logger.info(
            f'Parking lot "{lot.prime_location_name}" and all related spots deleted by admin {current_user.id}'
        )
        return redirect(url_for("admin.parking_lots"))

    except SQLAlchemyError as e:
        db.session.rollback()
        flash("An error occurred while saving to the database.", "danger")
        current_app.logger.error(f"Database error (delete lot): {str(e)}")
        return redirect(url_for("admin.delete_parking_lot", lot_id=lot_id))

    finally:
        db.session.close()


# User Management
# Displays and manages registered users.


@admin_bp.route("/registered-users")
@admin_required
def registered_users():
    """Displays all registered users."""
    users = User.query.filter_by(role=UserRole.USER).all()
    return render_template("admin/registered_users.html", users=users)


# Parking Spot Management
# Manages the deletion and details of parking spots.


@admin_bp.route("/view_delete_spot/<int:spot_id>", methods=["GET", "POST"])
@admin_required
def view_delete_spot(spot_id):
    """Handles the deletion of a single parking spot."""
    spot = ParkingSpot.query.get_or_404(spot_id)
    form = DeleteParkingSpotForm()

    if form.validate_on_submit():
        if spot.status == SpotStatus.OCCUPIED:
            flash("Cannot delete an occupied parking spot.", "danger")
            current_app.logger.warning(
                f"Attempt to delete occupied spot {spot.id} by admin {current_user.id}"
            )
            return redirect(url_for("admin.parking_lots"))

        try:
            spot.parking_lot.maximum_number_of_spots -= 1
            db.session.delete(spot)
            db.session.commit()

            flash("Spot deleted successfully!", "success")
            current_app.logger.info(
                f"Spot {spot.id} deleted by admin {current_user.id}"
            )
            return redirect(url_for("admin.parking_lots"))

        except SQLAlchemyError as e:
            db.session.rollback()
            flash("An error occurred while saving to the database.", "danger")
            current_app.logger.error(f"Database error (delete spot): {str(e)}")
            return redirect(url_for("admin.view_delete_spot", spot_id=spot_id))

        finally:
            db.session.close()

    form.spot_id.data = spot.id
    return render_template("admin/view_delete_spot.html", form=form, spot=spot)


@admin_bp.route("/occupied_spot-details/<int:spot_id>")
@admin_required
def occupied_spot_details(spot_id):
    """Displays details of an occupied parking spot."""
    reservation = ReservedParkingSpot.query.filter_by(spot_id=spot_id).first()

    # Calculate duration and estimated cost
    aware_parking_timestamp = (
        reservation.parking_timestamp.replace(tzinfo=IST)
        if reservation.parking_timestamp.tzinfo is None
        else reservation.parking_timestamp
    )
    duration_seconds = (datetime.now(IST) - aware_parking_timestamp).total_seconds()
    duration_hours = round(duration_seconds / 3600, 2)
    est_cost = round(duration_hours * reservation.parking_cost_per_hour, 2)

    return render_template(
        "admin/occupied_parking_spot_details.html",
        reservation=reservation,
        est_cost=est_cost,
    )


# Search Functionality
# Handles search functionality for parking lots, users, and vehicles.


@admin_bp.route("/search", methods=["GET", "POST"])
@admin_required
def search():
    """Handles search functionality for parking lots, users, and vehicles."""
    form = AdminSearchForm()
    lots, user, vehicle = [], None, None
    search_location = session.get("search_location", "")
    search_by = session.get("search_by", "")

    if form.validate_on_submit():
        search_location = form.search_value.data.strip()
        search_by = form.search_by.data.strip()
        session["search_location"] = search_location
        session["search_by"] = search_by

        if search_location == "":
            session.pop("search_location", None)

    # Perform search based on category
    if search_location:
        category = search_by
        if category in ["location", "pin_code"]:
            lots = ParkingLot.query.filter(
                or_(
                    ParkingLot.prime_location_name.ilike(f"%{search_location}%"),
                    ParkingLot.pin_code.ilike(f"%{search_location}%"),
                    ParkingLot.city.ilike(f"%{search_location}%"),
                    ParkingLot.district.ilike(f"%{search_location}%"),
                    ParkingLot.state.ilike(f"%{search_location}%"),
                )
            ).all()
        elif category in ["user_id", "full_name", "phone_number", "email"]:
            user = User.query.filter(
                or_(
                    User.id.ilike(f"%{search_location}%"),
                    User.email.ilike(f"%{search_location}%"),
                    User.phone_number.ilike(f"%{search_location}%"),
                    User.full_name.ilike(f"%{search_location}%"),
                )
            ).first()
        elif category == "vehicle_number":
            vehicle = Vehicle.query.filter(
                Vehicle.vehicle_number.ilike(f"%{search_location}%")
            ).first()

    form.search_value.data = search_location
    return render_template(
        "admin/search.html",
        form=form,
        lots=lots,
        search_location=search_location,
        user=user,
        vehicle=vehicle,
    )


@admin_bp.route("/clear-search")
@admin_required
def clear_search():
    """Clears the search session."""
    session.pop("search_location", None)
    session.pop("search_by", None)
    flash("Search cleared.", "info")
    current_app.logger.info(f"Search cleared by admin {current_user.id}")
    return redirect(url_for("admin.search"))


# Summary and Charts
# Generates summary pages and visualizations for parking lot data.


@admin_bp.route("/summary")
@admin_required
def summary():
    """Renders the summary page."""
    return render_template("admin/summary.html")


@admin_bp.route("/chart/revenue")
@admin_required
def revenue_chart():
    """Generates a pie chart for revenue from each parking lot with total revenue display."""
    lots = ParkingLot.query.filter_by(is_active=True).all()
    labels = [lot.prime_location_name for lot in lots]
    revenues = [lot.revenue for lot in lots]
    total_revenue = sum(revenues)

    fig, ax = plt.subplots(figsize=(6, 6))

    if not any(revenues):
        ax.text(
            0.5,
            0.5,
            "No Revenue Data",
            horizontalalignment="center",
            verticalalignment="center",
            fontsize=14,
            color="gray",
        )
    else:
        wedges, texts, autotexts = ax.pie(
            revenues,
            labels=labels,
            autopct="%1.1f%%",
            startangle=90,
            wedgeprops={"width": 0.4},
            textprops={"fontsize": 10},
        )

        ax.set_title("Revenue from Each Parking Lot", fontsize=14)

        # Add total revenue text
        ax.text(
            0.5,
            -0.05,
            f"Total Revenue: ₹{total_revenue:.2f}",
            ha="center",
            va="center",
            fontsize=12,
            bbox=dict(
                boxstyle="round,pad=0.4", facecolor="lightyellow", edgecolor="gray"
            ),
            transform=ax.transAxes,
        )

    fig.tight_layout()
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    plt.close(fig)

    return Response(output.getvalue(), mimetype="image/png")


@admin_bp.route("/chart/parking-lots")
@admin_required
def parking_summary_chart():
    """Generates a bar chart showing available vs. occupied spots."""
    parking_lots = ParkingLot.query.all()
    lot_names, available_counts, occupied_counts, total_counts = [], [], [], []

    for lot in parking_lots:
        lot_names.append(lot.prime_location_name)
        available_counts.append(lot.available_spots_count())
        occupied_counts.append(lot.occupied_spots)
        total_counts.append(lot.maximum_number_of_spots)

    fig, ax = plt.subplots(figsize=(10, 6))
    x = range(len(lot_names))

    ax.bar(
        x, available_counts, width=0.4, label="Available", color="green", align="center"
    )
    ax.bar(
        x,
        occupied_counts,
        width=0.4,
        bottom=available_counts,
        label="Occupied",
        color="red",
        align="center",
    )

    ax.set_xticks(x)
    ax.set_xticklabels(lot_names, rotation=45, ha="right")
    ax.set_ylabel("Number of Spots")
    ax.set_title("Available vs Occupied Parking Spots")
    ax.yaxis.grid(True, linestyle="--", linewidth=0.5, color="black", alpha=0.6)
    ax.legend()

    # Add labels on top of each bar
    for i, total in enumerate(total_counts):
        total_height = available_counts[i] + occupied_counts[i]
        ax.text(
            x=i,
            y=total_height + 1,
            s=f"{occupied_counts[i]}/{total}",
            ha="center",
            va="bottom",
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", alpha=0.8),
        )
    ax.set_ylim(0, max(total_counts) + 15)

    fig.tight_layout()
    canvas = FigureCanvas(fig)
    img_io = io.BytesIO()
    canvas.print_png(img_io)
    img_io.seek(0)
    plt.close(fig)

    return Response(img_io.getvalue(), mimetype="image/png")


@admin_bp.route("/download/parking-lot-summary")
@admin_required
def download_parking_lot_summary():
    """
    Generates an Excel file summarizing parking lots with revenue and spot stats including floor, open/close time.
    """
    lots = ParkingLot.query.all()
    data = []
    total_revenue = 0

    for lot in lots:
        name = lot.prime_location_name
        floor = lot.floor_level
        open_time = lot.open_time.strftime("%H:%M") if lot.open_time else "N/A"
        close_time = lot.close_time.strftime("%H:%M") if lot.close_time else "N/A"
        available = lot.available_spots_count()
        occupied = lot.occupied_spots
        max_spots = lot.maximum_number_of_spots
        revenue = lot.revenue
        total_revenue += revenue

        data.append(
            {
                "Parking Lot": name,
                "Floor Level": floor,
                "Open Time": open_time,
                "Close Time": close_time,
                "Available Spots": available,
                "Occupied Spots": occupied,
                "Total Spots": max_spots,
                "Revenue (₹)": revenue,
            }
        )

    if not data:
        data = [
            {
                "Parking Lot": "No Data",
                "Floor Level": "N/A",
                "Open Time": "N/A",
                "Close Time": "N/A",
                "Available Spots": 0,
                "Occupied Spots": 0,
                "Total Spots": 0,
                "Revenue (₹)": 0.0,
            }
        ]

    df = pd.DataFrame(data)

    # Add total revenue row
    df.loc[len(df.index)] = ["", "", "", "", "", "", "Total Revenue", total_revenue]

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Lot Summary")

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment;filename=parking_lot_summary_admin.xlsx"
        },
    )


# End of Admin Controller
