import os, json
from flask.views import MethodView
from flask import request, jsonify

from src.services.sheets import fetch_responses_df
from src.services.data_source import normalize_df
from src.services.calibration import calibrate
from src.services.agents import build_agent
from src.services.montecarlo import run_montecarlo
from src.services.sensitivity import sensitivity_by_estrato

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

class ApiMontecarlo(MethodView):
    def post(self):
        payload = request.get_json(force=True)

        # parámetros
        steps = int(payload.get("steps", 12))
        replicas = int(payload.get("replicas", 1000))
        umbral = float(payload.get("umbral", 0.60))

        params = payload.get("params", {})
        # defaults (tu esencia)
        sim_params = dict(
            p_crisis=float(params.get("p_crisis", 0.30)),
            lam_denuncias=float(params.get("lam_denuncias", 1.0)),
            mu_debate=float(params.get("mu_debate", 0.60)),
            sigma_debate=float(params.get("sigma_debate", 0.15)),
            phi_min=float(params.get("phi_min", 0.30)),
            phi_max=float(params.get("phi_max", 0.60)),
            alpha_min=float(params.get("alpha_min", 0.20)),
            alpha_max=float(params.get("alpha_max", 0.40)),
        )

        injected = payload.get("injected_shocks", {})  # {"4":{"D_add":3}}
        injected_shocks = {int(k): v for k, v in injected.items()}

        lealtad_estrato = payload.get("lealtad_estrato", {
            "Bajo": 0.80,
            "Medio-Bajo": 0.70,
            "Medio": 0.60,
            "Medio-Alto": 0.75
        })

        df = fetch_responses_df()
        df = normalize_df(df)
        agents = [build_agent(row) for _, row in df.iterrows()]

        betas = load_betas()

        # corre
        res = run_montecarlo(
            base_agents=agents,
            betas=betas,
            params=sim_params,
            steps=steps,
            n_replicas=replicas,
            contagio_umbral=umbral,
            lealtad_estrato=lealtad_estrato,
            injected_shocks=injected_shocks
        )

        # guardar muestras para RF 3.4
        _LAST_RUN["samples"] = res.get("samples", [])

        # además devolvemos serie promedio+IC95 por semana aproximado: aquí simplificado
        # (para no hacer Monte Carlo por timestep en este turno, usamos banda IC final y una réplica sample para la curva)
        sample_trace = _LAST_RUN["samples"][0]["trace"] if _LAST_RUN["samples"] else []

        return jsonify({
            "final": {
                "A": res["A"],
                "B": res["B"]
            },
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
