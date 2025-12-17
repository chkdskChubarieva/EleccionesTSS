from flask.views import MethodView
from flask import render_template
from src.services.config_service import is_survey_active

class DashboardController(MethodView):
    """Controlador para la vista principal del dashboard de simulación"""
    def get(self):
        estado_encuesta = is_survey_active()
        return render_template("dashboard.html", survey_active=estado_encuesta)

class DescriptivoController(MethodView):
    """Controlador para la vista de análisis descriptivo de la encuesta"""
    def get(self):
        return render_template("descriptivo.html")