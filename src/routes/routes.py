# src/routes/routes.py
from src.controllers.controller import EncuestaController
from src.controllers.dashboard_controller import DashboardController, DescriptivoController
from src.controllers.api_controller import ApiCalibrate, ApiMontecarlo, ApiScenario, ApiSensitivity
from src.controllers.auth_controller import LoginController, LogoutController, login_required

def register_routes(app):
    app.add_url_rule("/encuesta", view_func=EncuestaController.as_view("encuesta"), methods=["GET","POST"])

    app.add_url_rule("/login", view_func=LoginController.as_view("login"), methods=["GET", "POST"])
    app.add_url_rule("/logout", view_func=LogoutController.as_view("logout"), methods=["GET"])

   
    view_dash = login_required(DashboardController.as_view("dashboard"))
    app.add_url_rule("/", view_func=view_dash)

    view_desc = login_required(DescriptivoController.as_view("descriptivo"))
    app.add_url_rule("/descriptivo", view_func=view_desc)

    app.add_url_rule("/api/calibrate", view_func=login_required(ApiCalibrate.as_view("api_calibrate")), methods=["GET"])
    app.add_url_rule("/api/montecarlo", view_func=login_required(ApiMontecarlo.as_view("api_montecarlo")), methods=["POST"])
    app.add_url_rule("/api/scenario/<int:replica>", view_func=login_required(ApiScenario.as_view("api_scenario")), methods=["GET"])
    app.add_url_rule("/api/sensitivity", view_func=login_required(ApiSensitivity.as_view("api_sensitivity")), methods=["GET"])