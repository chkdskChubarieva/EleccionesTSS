import os, json
from flask.views import MethodView
from flask import request, jsonify
import math

from src.services.sheets import fetch_all_responses_as_df
from src.services.data_source import normalize_df
from src.services.calibration import calibrate
from src.services.agents import build_agent
from src.services.montecarlo import run_montecarlo
from src.services.sensitivity import sensitivity_by_estrato
from src.services.config_service import set_survey_active
import copy
from src.services.abm_engine import ABMSimulator

# cache en memoria para escenarios
_LAST_RUN = {"samples": []}

def _to_serializable(obj):
    """Convierte objetos no serializables a JSON (NaN -> null)"""
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_to_serializable(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    else:
        return obj

def _services_dir():
    base_dir = os.path.dirname(__file__)           # .../controllers
    return os.path.abspath(os.path.join(base_dir, "..", "services"))

def load_betas_abm():
    """
    Betas ANTIGUOS: beta0, betaE, betaD, betaP, betaR
    -> usados SOLO para la simulación (Monte Carlo + shocks).
    """
    betas_path = os.path.join(_services_dir(), "betas_sim_abm.json")
    with open(betas_path, "r", encoding="utf-8") as f:
        return json.load(f)

class ApiController(MethodView):
    def get(self, replica=None):
        return jsonify({"error": "Not implemented"}), 400

    def post(self):
        return jsonify({"error": "Not implemented"}), 400


class ApiCalibrate(MethodView):
    def get(self):
        df = fetch_all_responses_as_df()
        df = normalize_df(df)
        cal = calibrate(df)

        response_data = {
            "init_dist": cal.init_dist,
            "by_estrato": cal.by_estrato,
            "by_ideologia": cal.by_ideologia,
            "normals": cal.normals,
            "n": int(len(df))
        }
        # Limpiar valores NaN/Inf antes de serializar a JSON
        response_data = _to_serializable(response_data)
        return jsonify(response_data)


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

            # (opcional) pesos macro si luego quieres ajustar:
            "w_macro": float(p_raw.get("w_macro", 0.20))
        }

        # Shocks inyectados
        injected_raw = payload.get("injected_shocks", {})
        injected_shocks = {}
        for t_str, events_list in injected_raw.items():
            injected_shocks[int(t_str)] = events_list if isinstance(events_list, list) else []

        # Datos base
        df = fetch_all_responses_as_df()
        df = normalize_df(df)
        agents = [build_agent(row) for _, row in df.iterrows()]

        # ✅ AQUÍ: cargar betas ANTIGUOS para la simulación
        betas = load_betas_abm()
        lealtad_estrato = {
            "Bajo": 0.90,
            "Medio-Bajo": 0.95,
            "Medio": 1.00,
            "Medio-Alto": 1.08
        }
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

        idx = max(0, min(replica - 1, len(samples) - 1))
        return jsonify(samples[idx])


class ApiSensitivity(MethodView):
    def get(self):
        try:
            df = fetch_all_responses_as_df()
            df = normalize_df(df)

            # ✅ sensibilidad usa betas ACTUALES desde src/services/sensitivity.py
            rows = sensitivity_by_estrato(df)
            response_data = {"rows": rows or []}
            response_data = _to_serializable(response_data)
            return jsonify(response_data)
        except Exception as e:
            print(f"❌ Error en GET /api/sensitivity: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e), "rows": []}), 500

    def post(self):
        try:
            payload = request.get_json(force=True)

            f_lealtad = float(payload.get("factor_lealtad", 1.0))
            f_contagio = float(payload.get("factor_contagio", 1.0))
            f_ruido = float(payload.get("factor_ruido", 1.0))
            f_medios = float(payload.get("factor_medios", 1.0))
            f_memoria = float(payload.get("factor_memoria", 0.8))

            df = fetch_all_responses_as_df()
            df = normalize_df(df)

            # ✅ aquí SÍ pasamos sliders a la función real
            rows = sensitivity_by_estrato(
                df,
                factor_lealtad=f_lealtad,
                factor_contagio=f_contagio,
                factor_ruido=f_ruido,
                factor_medios=f_medios,
                factor_memoria=f_memoria,
                top_k=3
            )

            # ✅ PROYECCIÓN REAL (mini-ABM rápido)
            steps = 6
            replicas_fast = 160  # 120–220 (según rendimiento)

            # Parámetros del motor para sensibilidad (incluye sliders)
            sim_params = {
                "p_crisis": 0.3,
                "lam_denuncias": 1.0 * f_ruido,
                "mu_debate": 0.6,
                "sigma_debate": 0.15 * f_ruido,
                "phi_min": 0.3,
                "phi_max": 0.6,
                "w_macro": 0.20,
                "factor_lealtad": f_lealtad,
                "factor_medios": f_medios,
                "factor_memoria": f_memoria
            }

            # contagio: más contagio => umbral más fácil de activar
            base_umbral = 0.60
            umbral_eff = max(0.30, min(0.90, base_umbral / max(f_contagio, 0.1)))

            # lealtad por estrato (si ya lo aplicas en ABM)
            lealtad_estrato = {
                "Bajo": 0.90,
                "Medio-Bajo": 0.95,
                "Medio": 1.00,
                "Medio-Alto": 1.08
            }

            betas_abm = load_betas_abm()
            agents_base = [build_agent(row) for _, row in df.iterrows()]

            import random
            rng = random.Random(12345)

            sumA = [0.0] * steps
            sumB = [0.0] * steps

            for _ in range(replicas_fast):
                agents = copy.deepcopy(agents_base)

                sim = ABMSimulator(
                    agents=agents,
                    betas=betas_abm,
                    params=sim_params,
                    steps=steps,
                    contagio_umbral=umbral_eff,
                    lealtad_estrato=lealtad_estrato,
                    injected_shocks=None,
                    seed=rng.randrange(1, 10_000_000)
                )

                trace, _ = sim.run()
                for t in range(steps):
                    sumA[t] += float(trace[t].get("A", 0.0)) * 100.0
                    sumB[t] += float(trace[t].get("B", 0.0)) * 100.0

            proj_A = [round(x / replicas_fast, 3) for x in sumA]
            proj_B = [round(x / replicas_fast, 3) for x in sumB]

            response_data = {
                "rows": rows,
                "projection": {"A": proj_A, "B": proj_B}
            }
            response_data = _to_serializable(response_data)
            return jsonify(response_data)
        except Exception as e:
            print(f"❌ Error en POST /api/sensitivity: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e), "rows": [], "projection": {"A": [], "B": []}}), 500



class ApiToggleSurvey(MethodView):
    def post(self):
        data = request.get_json(force=True)
        new_status = bool(data.get("active"))
        set_survey_active(new_status)
        return jsonify({"success": True, "new_status": new_status})
