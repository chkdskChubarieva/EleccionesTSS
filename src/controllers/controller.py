from flask.views import MethodView
from flask import request, render_template, redirect, url_for
from src.services.sheets import append_google_forms_like
from src.services.config_service import is_survey_active
from src.services.survey_models import save_form_to_db
class EncuestaController(MethodView):
    def get(self):
        # VERIFICACIÓN: Si está cerrada, mostrar pantalla de bloqueo
        if not is_survey_active():
            return render_template("encuesta_cerrada.html")
            
        return render_template("encuesta.html")

    def post(self):
        if not is_survey_active():
            return render_template("encuesta_cerrada.html")

        form_dict = request.form.to_dict(flat=False)
        print("\n=== NUEVA RESPUESTA ===")
        print("=======================\n")

        append_google_forms_like(form_dict)
        try:
            ip = request.headers.get("X-Forwarded-For", request.remote_addr) or ""
            ua = request.headers.get("User-Agent", "") or ""
            save_form_to_db(form_dict, ip=ip, user_agent=ua)
        except Exception as e:
            print(f"[WARN] No se pudo guardar en MySQL(SQLAlchemy): {e}")
            
        return """
        <script>
            alert("¡Gracias por participar en la encuesta! 😃✅");
            window.location.href = "/encuesta";
        </script>
        """