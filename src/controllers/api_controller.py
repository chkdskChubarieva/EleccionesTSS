import os, json
from flask.views import MethodView
from flask import request, jsonify

from src.services.sheets import fetch_responses_df
from src.services.data_source import normalize_df
from src.services.calibration import calibrate
from src.services.agents import build_agent
from src.services.montecarlo import run_montecarlo
from src.services.sensitivity import sensitivity_by_estrato
from src.services.config_service import set_survey_active

# cache en memoria para escenarios
_LAST_RUN = {"samples": []}

def load_betas():
    base_dir = os.path.dirname(__file__)           # .../controllers
    services_dir = os.path.abspath(os.path.join(base_dir, "..", "services"))
    betas_path = os.path.join(services_dir, "betas_sim.json")
    with open(betas_path, "r", encoding="utf-8") as f:
        return json.load(f)

class ApiController(MethodView):
    def get(self, replica=None):
        # decide según endpoint: flask usa el mismo view_func, así que lo separamos por path en routes.
        return jsonify({"error": "Not implemented"}), 400

    def post(self):
        return jsonify({"error": "Not implemented"}), 400

# Helpers “tipo views”
class ApiCalibrate(MethodView):
    def get(self):
        df = fetch_responses_df()
        df = normalize_df(df)
        cal = calibrate(df)

        # para RF 3.1
        return jsonify({
            "init_dist": cal.init_dist,
            "by_estrato": cal.by_estrato,
            "by_ideologia": cal.by_ideologia,
            "normals": cal.normals,
            "n": int(len(df))
        })

# Modificar SOLO el método post de ApiMontecarlo
class ApiMontecarlo(MethodView):
    def post(self):
        payload = request.get_json(force=True)

        # parámetros básicos
        steps = int(payload.get("steps", 12))
        replicas = int(payload.get("replicas", 1000))
        umbral = float(payload.get("umbral", 0.60))
        
        # Parámetros del motor base
        p_raw = payload.get("params", {})
        sim_params = {
            "p_crisis": float(p_raw.get("p_crisis", 0.3)),
            "lam_denuncias": float(p_raw.get("lam_denuncias", 1.0)),
            "mu_debate": float(p_raw.get("mu_debate", 0.6)),
            "sigma_debate": float(p_raw.get("sigma_debate", 0.15)),
            "phi_min": float(p_raw.get("phi_min", 0.3)),
            "phi_max": float(p_raw.get("phi_max", 0.6)),
        }

        # === NUEVO: Procesamiento de Shocks ===
        # Estructura esperada: { "4": [ {"target":"A", "topic":"corrupcion", ...} ] }
        injected_raw = payload.get("injected_shocks", {})
        injected_shocks = {}
        
        for t_str, events_list in injected_raw.items():
            if isinstance(events_list, list):
                injected_shocks[int(t_str)] = events_list
            else:
                # Soporte legacy por si acaso
                injected_shocks[int(t_str)] = []

        df = fetch_responses_df()
        df = normalize_df(df)
        agents = [build_agent(row) for _, row in df.iterrows()]
        betas = load_betas()

        res = run_montecarlo(
            base_agents=agents,
            betas=betas,
            params=sim_params,
            steps=steps,
            n_replicas=replicas,
            contagio_umbral=umbral,
            injected_shocks=injected_shocks # Pasamos la nueva estructura
        )

        _LAST_RUN["samples"] = res.get("samples", [])
        sample_trace = _LAST_RUN["samples"][0]["trace"] if _LAST_RUN["samples"] else []

        return jsonify({
            "final": res, 
            "sample_trace": sample_trace,
            "replicas_stored": len(_LAST_RUN["samples"])
        })

class ApiScenario(MethodView):
    def get(self, replica: int):
        samples = _LAST_RUN.get("samples", [])
        if not samples:
            return jsonify({"error": "No hay corrida previa. Ejecuta Monte Carlo primero."}), 400

        # replica es 1..N en UI (nosotros guardamos pocas)
        idx = max(0, min(replica - 1, len(samples) - 1))
        return jsonify(samples[idx])

class ApiSensitivity(MethodView):
    def get(self):
        df = fetch_responses_df()
        df = normalize_df(df)
        rows = sensitivity_by_estrato(df)
        return jsonify({"rows": rows})

class ApiToggleSurvey(MethodView):
    def post(self):
        data = request.get_json(force=True)
        new_status = bool(data.get("active"))
        set_survey_active(new_status)
        return jsonify({"success": True, "new_status": new_status})