# src/routes/routes.py
from src.controllers.controller import EncuestaController
from src.controllers.dashboard_controller import DashboardController
from src.controllers.api_controller import ApiCalibrate, ApiMontecarlo, ApiScenario
from src.controllers.api_controller import ApiSensitivity

def register_routes(app):
    app.add_url_rule("/", view_func=DashboardController.as_view("dashboard"))
    app.add_url_rule("/encuesta", view_func=EncuestaController.as_view("encuesta"), methods=["GET","POST"])

    app.add_url_rule("/api/calibrate", view_func=ApiCalibrate.as_view("api_calibrate"), methods=["GET"])
    app.add_url_rule("/api/montecarlo", view_func=ApiMontecarlo.as_view("api_montecarlo"), methods=["POST"])
    app.add_url_rule("/api/scenario/<int:replica>", view_func=ApiScenario.as_view("api_scenario"), methods=["GET"])
    app.add_url_rule("/api/sensitivity", view_func=ApiSensitivity.as_view("api_sensitivity"), methods=["GET"])
