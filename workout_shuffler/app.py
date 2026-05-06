from flask import Flask
from config import Config
from services.db import Database
from models.workout_manager import WorkoutManager
from routes.plan_routes import plan_bp
from routes.suggestion_routes import suggestion_bp
from routes.history_routes import history_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = 'workout-shuffler-secret-2024'

    cfg = Config()
    db = Database(cfg.DATABASE_URL)
    db.init_db()

    manager = WorkoutManager(db)
    app.config['manager'] = manager
    app.config['GEMINI_API_KEY'] = cfg.GEMINI_API_KEY

    app.register_blueprint(plan_bp)
    app.register_blueprint(suggestion_bp)
    app.register_blueprint(history_bp)

    return app


if __name__ == '__main__':
    create_app().run(debug=True)
