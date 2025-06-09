from .auth import auth_bp
from .local import local_bp

def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(local_bp)
