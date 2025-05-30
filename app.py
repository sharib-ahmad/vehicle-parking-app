from flask import Flask
from models import db
import os 

app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'vehicle_parking_app.sqlite3')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'f56ae947f162336cb881dc9d354f3f4e6bb092c432065c3a'

db.init_app(app)



if __name__ == '__main__':
    app.run()