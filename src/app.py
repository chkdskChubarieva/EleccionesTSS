# src/app.py
import os
from dotenv import load_dotenv
from flask import Flask

from src.controllers.errors import not_found
from src.routes.routes import register_routes
from src.extensions import db

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "dev-secret")  # mejor desde .env

    # ✅ SQLAlchemy SOLO para encuesta
    user = os.getenv("MYSQL_USER", "elecciones_app")
    pw = os.getenv("MYSQL_PASSWORD", "ClaveFuerte123")
    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    port = os.getenv("MYSQL_PORT", "3306")
    name = os.getenv("MYSQL_DB", "elecciones_tss")

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://{user}:{pw}@{host}:{port}/{name}?charset=utf8mb4"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # ✅ Importar modelos (solo para que SQLAlchemy los registre)
    with app.app_context():
        from src.services import survey_models  # NO importes Encuesta,Respuesta directo
        db.create_all()

    register_routes(app)
    app.register_error_handler(404, not_found)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
