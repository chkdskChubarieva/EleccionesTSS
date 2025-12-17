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

    def post(self):
        payload = request.get_json(force=True)
        
        # 1. Recuperar TODAS las variables
        f_lealtad = float(payload.get("factor_lealtad", 1.0))
        f_contagio = float(payload.get("factor_contagio", 1.0))
        f_ruido = float(payload.get("factor_ruido", 1.0))
        f_medios = float(payload.get("factor_medios", 1.0))   # Nuevo
        f_memoria = float(payload.get("factor_memoria", 0.8)) # Nuevo

        # Cargar datos base para la tabla (RF 3.3)
        df = fetch_responses_df()
        df = normalize_df(df)
        
        # Aquí llamarías a tu función real de sensibilidad pasando los factores
        # rows = sensitivity_by_estrato(df, lealtad=f_lealtad, ...)
        rows = sensitivity_by_estrato(df) 

        # 2. Lógica de Proyección Visual (Simulación Rápida)
        # Creamos una curva base y la deformamos según tus variables
        
        base_A = [40, 41, 40, 42, 43, 44] # Tendencia base Candidato A
        base_B = [30, 29, 31, 30, 28, 27] # Tendencia base Candidato B
        
        proj_A = []
        proj_B = []

        for t, (a, b) in enumerate(zip(base_A, base_B)):
            
            avg_a = 40
            desvio = (a - avg_a) * f_medios * f_contagio
            
            val_a = avg_a + (desvio / f_lealtad)
            
            import random
            ruido = (random.random() - 0.5) * 2 * f_ruido
            
            proj_A.append(val_a + ruido)
            
            proj_B.append(b / f_lealtad - (ruido))

        return jsonify({
            "rows": rows,
            "projection": {
                "A": proj_A,
                "B": proj_B
            }
        })

class ApiToggleSurvey(MethodView):
    def post(self):
        data = request.get_json(force=True)
        new_status = bool(data.get("active"))
        set_survey_active(new_status)
        return jsonify({"success": True, "new_status": new_status})
