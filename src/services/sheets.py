# src/services/sheets.py
import os, json, datetime, pytz, gspread
from google.oauth2.service_account import Credentials
import pandas as pd

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
# Leemos credenciales de variables de entorno
CREDS_FILE = os.getenv("GOOGLE_SA_JSON")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
WORKSHEET_NAME = os.getenv("WORKSHEET_NAME", "Respuestas")

# === Etiquetas para GUARDAR respuestas (Mantiene compatibilidad con tu formulario) ===
FIELD_LABELS = {
    "edad": "Edad",
    "genero": "Género",
    "departamento": "Departamento",
    "provincia": "Provincia / Localidad",
    "situacion": "Situación educativa",
    "carrera_est": "Carrera (estudiante)",
    "carrera_prof": "Carrera (profesional)",
    "area_prof": "Área profesional",
    "estrato": "Estrato socioeconómico",
    "internet_diario": "Tiempo de conexión a internet por día",
    "estatus_laboral": "Estatus laboral",
    "servicios": "Acceso a servicios básicos",
    "intencion_voto": "Si las elecciones fueran mañana, ¿por quién votarías?",
    "seguridad_voto": "¿Qué tan seguro estás de tu elección? (1-5)",
    "evento_determinante": "¿Qué tipo de evento te haría cambiar de opinión respecto a los candidatos?",
    "evento_otro": "Evento determinante (otro, especificar)",
    "interes_politica": "Interés por la política nacional (slider)",
    "frecuencia_conversacion": "Frecuencia con la que conversas sobre política (slider)",
    "alineamiento": "Alineamiento ideológico personal",
    
    # Factores (s3)
    "s3_economia": "Factores decisión: Economía (1-5)",
    "s3_educacion": "Factores decisión: Educación (1-5)",
    "s3_corrupcion_justicia": "Factores decisión: Corrupción/Justicia (1-5)",
    "s3_servicios": "Factores decisión: Servicios públicos (1-5)",
    "s3_seguridad": "Factores decisión: Seguridad ciudadana (1-5)",
    "s3_medioambiente": "Factores decisión: Medio ambiente (1-5)",
    "s3_derechos": "Factores decisión: Derechos sociales (1-5)",
    "s3_modelo_desarrollo": "Factores decisión: Modelo de desarrollo (1-5)",

    # Atributos Rodrigo
    "attr_rodrigo_1": "Rodrigo Paz - Experiencia en gestión (1-5)",
    "attr_rodrigo_2": "Rodrigo Paz - Honestidad/Transparencia (1-5)",
    "attr_rodrigo_3": "Rodrigo Paz - Capacidad de unir a la población (1-5)",
    "attr_rodrigo_4": "Rodrigo Paz - Conexión con los jóvenes (1-5)",
    "attr_rodrigo_5": "Rodrigo Paz - Liderazgo fuerte/Decisivo (1-5)",
    "attr_rodrigo_6": "Rodrigo Paz - Propuestas claras y realistas (1-5)",
    "attr_rodrigo_7": "Rodrigo Paz - Coherencia discurso/acciones (1-5)",
    "attr_rodrigo_8": "Rodrigo Paz - Empatía con sectores vulnerables (1-5)",
    "attr_rodrigo_9": "Rodrigo Paz - Competencia técnica/Académica (1-5)",
    "attr_rodrigo_10": "Rodrigo Paz - Cercanía con la realidad boliviana (1-5)",

    # Atributos Tuto
    "attr_tuto_1": "Tuto Quiroga - Experiencia en gestión (1-5)",
    "attr_tuto_2": "Tuto Quiroga - Honestidad/Transparencia (1-5)",
    "attr_tuto_3": "Tuto Quiroga - Capacidad de unir a la población (1-5)",
    "attr_tuto_4": "Tuto Quiroga - Conexión con los jóvenes (1-5)",
    "attr_tuto_5": "Tuto Quiroga - Liderazgo fuerte/Decisivo (1-5)",
    "attr_tuto_6": "Tuto Quiroga - Propuestas claras y realistas (1-5)",
    "attr_tuto_7": "Tuto Quiroga - Coherencia discurso/acciones (1-5)",
    "attr_tuto_8": "Tuto Quiroga - Empatía con sectores vulnerables (1-5)",
    "attr_tuto_9": "Tuto Quiroga - Competencia técnica/Académica (1-5)",
    "attr_tuto_10": "Tuto Quiroga - Cercanía con la realidad boliviana (1-5)",

    "medio_influencia": "Medio de influencia (selección múltiple)",

    # Expectativas
    "expectativa_futuro": "Expectativa de futuro profesional",
    "cond_oportunidades": "Mercado laboral: oportunidades para jóvenes",
    "cond_demanda_carrera": "Mercado laboral: demanda de mi carrera",
    "cond_acceso_formal": "Mercado laboral: accesibilidad a empleos formales",

    # Problemáticas
    "prob_crisis": "Prioridad: Crisis económica y desempleo (1-5)",
    "prob_combustible": "Prioridad: Combustible/recursos energéticos (1-5)",
    "prob_transporte": "Prioridad: Transporte público (1-5)",
    "prob_corrupcion": "Prioridad: Corrupción/Desconfianza institucional (1-5)",
    "prob_seguridad": "Prioridad: Seguridad ciudadana (1-5)",
    "prob_salud_educacion": "Prioridad: Salud y educación pública (1-5)",
    "prob_medioambiente": "Prioridad: Medio ambiente/gestión de residuos (1-5)",

    # Trayectorias
    "trayectoria_influye": "Influencia del pasado del candidato (1-5)",
    "trayectoria_conocimiento": "Conocimiento del historial de candidatos (1-5)",
    "vp_importancia": "Importancia del rol del vicepresidente (1-5)",
}

# Lista ordenada de encabezados base
BASE_HEADERS = [
    "Timestamp (GMT-4)",
    FIELD_LABELS["edad"], FIELD_LABELS["genero"], FIELD_LABELS["departamento"], FIELD_LABELS["provincia"],
    FIELD_LABELS["situacion"], FIELD_LABELS["carrera_est"], FIELD_LABELS["carrera_prof"], FIELD_LABELS["area_prof"],
    FIELD_LABELS["estrato"], FIELD_LABELS["internet_diario"], FIELD_LABELS["estatus_laboral"], FIELD_LABELS["servicios"],
    FIELD_LABELS["intencion_voto"], FIELD_LABELS["seguridad_voto"], FIELD_LABELS["evento_determinante"], FIELD_LABELS["evento_otro"],
    FIELD_LABELS["interes_politica"], FIELD_LABELS["frecuencia_conversacion"], FIELD_LABELS["alineamiento"],
    # ... (Factores)
    FIELD_LABELS["s3_economia"], FIELD_LABELS["s3_educacion"], FIELD_LABELS["s3_corrupcion_justicia"],
    FIELD_LABELS["s3_servicios"], FIELD_LABELS["s3_seguridad"], FIELD_LABELS["s3_medioambiente"],
    FIELD_LABELS["s3_derechos"], FIELD_LABELS["s3_modelo_desarrollo"],
    # ... (Atributos)
    FIELD_LABELS["attr_rodrigo_1"], FIELD_LABELS["attr_rodrigo_2"], FIELD_LABELS["attr_rodrigo_3"], FIELD_LABELS["attr_rodrigo_4"], FIELD_LABELS["attr_rodrigo_5"],
    FIELD_LABELS["attr_rodrigo_6"], FIELD_LABELS["attr_rodrigo_7"], FIELD_LABELS["attr_rodrigo_8"], FIELD_LABELS["attr_rodrigo_9"], FIELD_LABELS["attr_rodrigo_10"],
    FIELD_LABELS["attr_tuto_1"], FIELD_LABELS["attr_tuto_2"], FIELD_LABELS["attr_tuto_3"], FIELD_LABELS["attr_tuto_4"], FIELD_LABELS["attr_tuto_5"],
    FIELD_LABELS["attr_tuto_6"], FIELD_LABELS["attr_tuto_7"], FIELD_LABELS["attr_tuto_8"], FIELD_LABELS["attr_tuto_9"], FIELD_LABELS["attr_tuto_10"],
    FIELD_LABELS["medio_influencia"],
    # ... (Resto)
    FIELD_LABELS["expectativa_futuro"], FIELD_LABELS["cond_oportunidades"], FIELD_LABELS["cond_demanda_carrera"], FIELD_LABELS["cond_acceso_formal"],
    FIELD_LABELS["prob_crisis"], FIELD_LABELS["prob_combustible"], FIELD_LABELS["prob_transporte"], FIELD_LABELS["prob_corrupcion"],
    FIELD_LABELS["prob_seguridad"], FIELD_LABELS["prob_salud_educacion"], FIELD_LABELS["prob_medioambiente"],
    FIELD_LABELS["trayectoria_influye"], FIELD_LABELS["trayectoria_conocimiento"], FIELD_LABELS["vp_importancia"],
]

def _client():
    """Autentica y devuelve el cliente de gspread"""
    # Opción 1: Credenciales en línea (Variable de entorno completa)
    inline = os.getenv("GOOGLE_SA_JSON_INLINE")
    if inline:
        try:
            info = json.loads(inline)
            creds = Credentials.from_service_account_info(info, scopes=SCOPES)
            return gspread.authorize(creds)
        except Exception as e:
            print(f"Error cargando credenciales inline: {e}")

    # Opción 2: Archivo físico
    if not CREDS_FILE or not os.path.exists(CREDS_FILE):
        print("⚠️ No se encontró el archivo de credenciales GOOGLE_SA_JSON.")
        # Retorna None o lanza error según prefieras, aquí lanzamos para depurar
        raise FileNotFoundError(f"Falta archivo de credenciales en: {CREDS_FILE}")
        
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    return gspread.authorize(creds)

def _open_ws():
    """Abre la hoja de cálculo y la pestaña correcta"""
    gc = _client()
    try:
        sh = gc.open_by_key(SPREADSHEET_ID)
    except Exception as e:
        raise ValueError(f"No se pudo abrir Spreadsheet ID {SPREADSHEET_ID}. Error: {e}")

    try:
        ws = sh.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        # Si no existe, la crea
        ws = sh.add_worksheet(title=WORKSHEET_NAME, rows=2000, cols=len(BASE_HEADERS))
    return ws

def _ensure_columns_strict(ws, want_headers):
    """Garantiza que la cabecera sea consistente"""
    current_header = ws.row_values(1)
    if len(current_header) != len(want_headers):
        ws.resize(rows=ws.row_count, cols=len(want_headers))
    
    if current_header != want_headers:
        if current_header:
            ws.delete_rows(1)
        ws.insert_row(want_headers, 1)
    return want_headers

def _form_to_payload(form_dict):
    """Convierte los datos del form HTML a formato Sheets usando las etiquetas"""
    payload = {}
    for name, values in form_dict.items():
        label = FIELD_LABELS.get(name, name)
        if isinstance(values, list):
            payload[label] = ", ".join(str(v) for v in values) if len(values)>1 else (str(values[0]) if values else "")
        else:
            payload[label] = str(values)
    return payload

def append_google_forms_like(form_dict: dict):
    """Guarda una respuesta nueva al final de la hoja"""
    try:
        ws = _open_ws()
        payload = _form_to_payload(form_dict)

        # Manejo de columnas extras dinámicas
        extras = [k for k in payload.keys() if k not in BASE_HEADERS and k != "Timestamp (GMT-4)"]
        extras.sort()
        want_headers = list(BASE_HEADERS) + extras

        header = _ensure_columns_strict(ws, want_headers)

        tz_bo = pytz.timezone("America/La_Paz")
        now_local = datetime.datetime.now(tz_bo).strftime("%Y-%m-%d %H:%M:%S")

        row_values = []
        for h in header:
            if h == "Timestamp (GMT-4)":
                row_values.append(now_local)
            else:
                row_values.append(payload.get(h, ""))
        
        ws.append_row(row_values, value_input_option="USER_ENTERED")
        print("✅ Respuesta guardada en Google Sheets exitosamente.")
    except Exception as e:
        print(f"❌ Error guardando en Sheets: {e}")

def fetch_all_responses_as_df():
    """
    Lee todas las respuestas de Google Sheets y devuelve DataFrame.
    Esta es la función que usa data_source.py
    """
    try:
        ws = _open_ws()
        records = ws.get_all_records() # Lee usando la fila 1 como encabezados
        if not records:
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        return df
    except Exception as e:
        print(f"❌ Error leyendo Sheets: {e}")
        return pd.DataFrame() # Retorna vacío en caso de error