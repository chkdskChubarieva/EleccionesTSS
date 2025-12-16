# src/app.py
from dotenv import load_dotenv
from flask import Flask
from src.routes.routes import register_routes
from src.controllers.errors import not_found

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = "dev-secret"  # cambia luego

    register_routes(app)
    app.register_error_handler(404, not_found)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
