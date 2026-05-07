from flask import Flask
from flask_login import LoginManager
from config import Config
from services.db import Database
from models.workout_manager import WorkoutManager
from routes.plan_routes import plan_bp
from routes.suggestion_routes import suggestion_bp
from routes.history_routes import history_bp
from routes.auth_routes import auth_bp

login_manager = LoginManager()


def create_app() -> Flask:
    app = Flask(__name__)
    cfg = Config()
    app.secret_key = cfg.SECRET_KEY

    db = Database(cfg.DATABASE_URL)
    db.init_db()

    manager = WorkoutManager(db)
    app.config['manager'] = manager
    app.config['GEMINI_API_KEY'] = cfg.GEMINI_API_KEY
    app.config['DEBUG'] = cfg.DEBUG

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'error'

    @login_manager.user_loader
    def load_user(user_id):
        return manager.get_user_by_id(int(user_id))

    app.register_blueprint(auth_bp)
    app.register_blueprint(plan_bp)
    app.register_blueprint(suggestion_bp)
    app.register_blueprint(history_bp)

    return app


if __name__ == '__main__':
    _app = create_app()
    _app.run(debug=_app.config['DEBUG'])
