"""
# Local/Public Controller
# This module handles public-facing routes for the application, such as the home, about, and contact pages.
"""

from flask import Blueprint, render_template,redirect,url_for


# Blueprint Initialization
# Sets up the local blueprint for public routes.

local_bp = Blueprint('local', __name__)

# Routes
# Defines public-facing routes for the application.

@local_bp.route('/')
def index():
    """Renders the home page."""
    return render_template('index.html')

@local_bp.route('/about')
def about():
    """Renders the about page."""
    return render_template('about.html')

@local_bp.route('/contact')
def contact():
    """Renders the contact page."""
    return render_template('contact.html')

@local_bp.route('/swagger')
def swagger():
    return redirect('/swagger/')

# End of Local/Public Controller