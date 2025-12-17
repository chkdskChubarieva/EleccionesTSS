import json
import os

CONFIG_FILE = "system_config.json"

def get_config():
    if not os.path.exists(CONFIG_FILE):
        # Configuración por defecto 
        return {"survey_active": True}
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {"survey_active": True}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def is_survey_active():
    cfg = get_config()
    return cfg.get("survey_active", True)

def set_survey_active(status: bool):
    cfg = get_config()
    cfg["survey_active"] = status
    save_config(cfg)