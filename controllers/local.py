from flask import Blueprint, render_template


local_bp = Blueprint('local', __name__)

@local_bp.route('/')
def index():
    return render_template('index.html')



@local_bp.route('/about')
def about():
    return render_template('about.html')

@local_bp.route('/contact')
def contact():
    return render_template('contact.html')