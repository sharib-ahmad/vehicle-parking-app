from flask import Flask
from models import db, login_manager ,csrf, User, create_admin_user
from controllers import register_blueprints
import os 
import logging
from logging.handlers import RotatingFileHandler


app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'vehicle_parking_app.sqlite3')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'f56ae947f162336cb881dc9d354f3f4e6bb092c432065c3a'

db.init_app(app)
login_manager.init_app(app)
csrf.init_app(app)
register_blueprints(app)
login_manager.login_view = 'auth.login'

# --- User loader for Flask-Login ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# --- Create Logs Folder & Setup Logging ---
if not os.path.exists('logs'):
    os.mkdir('logs')

file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=3)
file_handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
))
file_handler.setLevel(logging.INFO)

app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('App started and logging is set up.')

# --- Create Admin and Tables ---
with app.app_context():
    db.create_all()
    create_admin_user(app)



if __name__ == '__main__':
    app.run()