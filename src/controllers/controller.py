# src/controllers/controller.py
from flask.views import MethodView
from flask import request, render_template, redirect, url_for
from src.services.sheets import append_google_forms_like

class EncuestaController(MethodView):
    def get(self):
        return render_template("encuesta.html")

    def post(self):
        form_dict = request.form.to_dict(flat=False)

        print("\n=== NUEVA RESPUESTA ===")
        for k, v in form_dict.items():
            print(f"{k}: {v}")
        print("=======================\n")

        append_google_forms_like(form_dict)

        return """
        <script>
            alert("¡Gracias por participar en la encuesta! 😃✅");
            window.location.href = "/encuesta";
        </script>
        """
