from flask.views import MethodView
from flask import render_template

class DashboardController(MethodView):
    """Controlador para la vista principal del dashboard de simulación"""
    def get(self):
        return render_template("dashboard.html")

class DescriptivoController(MethodView):
    """Controlador para la vista de análisis descriptivo de la encuesta"""
    def get(self):
        return render_template("descriptivo.html")  

class AnalisisController(MethodView):
    """Controlador para la vista de análisis de sensibilidad"""
    def get(self):
        return render_template("analisis.html")