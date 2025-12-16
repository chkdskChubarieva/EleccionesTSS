from flask.views import MethodView
from flask import render_template

class DashboardController(MethodView):
    def get(self):
        return render_template("dashboard.html")
