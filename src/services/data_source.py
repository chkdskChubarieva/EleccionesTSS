import pandas as pd
import numpy as np
from typing import Optional, Dict
from src.services.sheets import fetch_all_responses_as_df


# Mapeo de valores de voto
COLUMN_MAPPING = {
    # Pregunta en Sheets (parte clave) : Variable Interna
    "estrato": "estrato_socioeconomico",
    "alineamiento": "alineamiento_ideologico",
    "seguro estás": "seguridad_1a5",
    "si las elecciones fueran hoy": "intencion_voto",
    "intención de voto": "intencion_voto",
    "interés por la política": "interes_politica",
    "frecuencia con la que conversas": "frecuencia_conversacion"
}

MAP_VOTO = {
    "Jorge Quiroga": "A",
    "Tuto": "A",
    "Quiroga": "A",
    "Rodrigo Paz": "B",
    "Paz Pereira": "B",
    "Blanco": "Blanco",
    "Nulo": "Nulo",
    "Indeciso": "Indeciso",
    "No lo sé": "Indeciso"
}

def fetch_responses_df(encuesta_id: int = 1, only_active: bool = True) -> pd.DataFrame:
    """
    Obtiene los datos DIRECTAMENTE de Google Sheets.
    Ignora MySQL para la lógica de simulación.
    """
    print("--- 📡 Conectando a Google Sheets... ---")
    try:
        # Intentamos obtener el DF desde el servicio de sheets
        # Si tu función en sheets.py se llama diferente, ajusta esta línea:
        df = fetch_all_responses_as_df() 
        
        if df.empty:
            print("⚠️ Alerta: Google Sheets devolvió un DataFrame vacío.")
            return pd.DataFrame()
            
        print(f"✅ Datos recibidos de Sheets: {len(df)} filas.")
        return df
        
    except Exception as e:
        print(f"❌ Error crítico leyendo Google Sheets: {e}")
        # Retornamos DF vacío para no romper la app
        return pd.DataFrame()


def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza y limpia los datos crudos de Sheets para que el Dashboard los entienda.
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # 1. Normalizar Nombres de Columnas (Busqueda difusa)
    # Buscamos columnas que contengan palabras clave y las renombramos
    renames = {}
    for col in df.columns:
        col_lower = str(col).lower()
        for key_phrase, target_col in COLUMN_MAPPING.items():
            if key_phrase in col_lower:
                renames[col] = target_col
                break # Ya encontramos match para esta columna
    
    if renames:
        df = df.rename(columns=renames)
        print(f"🔄 Columnas renombradas: {list(renames.values())}")

    # 2. Garantizar columnas críticas (Fillna seguro)
    
    # --- ESTRATO ---
    if 'estrato_socioeconomico' not in df.columns:
        df['estrato_socioeconomico'] = 'Medio'
    df['estrato'] = df['estrato_socioeconomico'].fillna('Medio').astype(str)

    # --- IDEOLOGÍA ---
    if 'alineamiento_ideologico' not in df.columns:
        df['alineamiento_ideologico'] = 'Centro'
    df['ideologia'] = df['alineamiento_ideologico'].fillna('Centro').astype(str)

    # --- INTENCIÓN DE VOTO ---
    # Buscamos la columna de voto (ya renombrada o buscamos de nuevo)
    col_voto = None
    if 'intencion_voto' in df.columns:
        col_voto = 'intencion_voto'
    else:
        # Intentar encontrarla por palabras clave
        for col in df.columns:
            col_lower = str(col).lower()
            if 'elecciones' in col_lower or 'votarías' in col_lower or 'voto' in col_lower:
                col_voto = col
                break
    
    print(f"🔍 Columna de voto detectada: {col_voto}")
    print(f"📊 Columnas disponibles: {list(df.columns)}")
    
    if col_voto:
        def limpiar_voto(val):
            val_str = str(val).lower().strip()
            for key, code in MAP_VOTO.items():
                if key.lower() in val_str:
                    return code
            return "Indeciso"
        
        df['estado_inicial'] = df[col_voto].apply(limpiar_voto)
        print(f"✅ Estado inicial creado. Distribución: {df['estado_inicial'].value_counts().to_dict()}")
    else:
        print("⚠️ No se encontró columna de voto, asignando Indeciso a todos")
        df['estado_inicial'] = 'Indeciso'

    # --- SEGURIDAD ---
    if 'seguridad_1a5' in df.columns:
        # A veces viene como "3 - Poco seguro", extraemos el número
        def extraer_num(val):
            try:
                return float(str(val).split()[0])
            except:
                return 3.0
        df['seguridad_1a5'] = df['seguridad_1a5'].apply(extraer_num).fillna(3.0)
    else:
        df['seguridad_1a5'] = 3.0

    # --- OTROS ---
    df['agent_id'] = range(1, len(df) + 1)
    if 'medio_influencia' in df.columns:
        df['medios'] = df['medio_influencia'].fillna('').astype(str)
    else:
        df['medios'] = ''
    
    return df

def get_encuesta_activa() -> Optional[Dict]:
    """Obtiene la encuesta actualmente habilitada"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM encuestas 
                WHERE habilitada = TRUE 
                ORDER BY fecha_inicio DESC 
                LIMIT 1
            """)
            return cursor.fetchone()
    except Error as e:
        print(f"✗ Error al obtener encuesta activa: {e}")
        return None

def insertar_respuesta(data: Dict, encuesta_id: int = 1) -> bool:
    """
    Inserta una nueva respuesta desde el formulario web
    
    Args:
        data: Diccionario con los datos del formulario
        encuesta_id: ID de la encuesta
        
    Returns:
        True si se insertó correctamente
    """
    import hashlib
    from datetime import datetime
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Generar hash anónimo
            timestamp = datetime.now().isoformat()
            hash_data = f"{timestamp}-{data.get('departamento', '')}-{os.urandom(16).hex()}"
            hash_anonimo = hashlib.sha256(hash_data.encode()).hexdigest()
            
            # IP hash (de la request)
            ip_hash = hashlib.sha256(f"web-{os.urandom(8).hex()}".encode()).hexdigest()
            
            # Procesar arrays
            import json
            servicios = json.dumps(data.getlist('servicios')) if 'servicios' in data else None
            medios = json.dumps(data.getlist('medio_influencia')) if 'medio_influencia' in data else None
            
            # Atributos de candidatos (se reciben como attr_rodrigo_1, attr_rodrigo_2, etc.)
            atributos_rodrigo = []
            atributos_tuto = []
            for i in range(1, 11):
                atributos_rodrigo.append(int(data.get(f'attr_rodrigo_{i}', 3)))
                atributos_tuto.append(int(data.get(f'attr_tuto_{i}', 3)))
            
            # Query de inserción
            query = """
            INSERT INTO respuestas (
                encuesta_id, hash_anonimo, ip_hash,
                edad, genero, departamento, provincia, situacion_educativa,
                carrera, area_profesional, estrato_socioeconomico,
                tiempo_internet, estatus_laboral, servicios_basicos,
                intencion_voto, seguridad_voto, evento_determinante, evento_otro,
                interes_politica, frecuencia_conversacion, alineamiento_ideologico,
                factor_economia, factor_educacion, factor_corrupcion, factor_servicios,
                factor_seguridad, factor_medioambiente, factor_derechos, factor_modelo_desarrollo,
                atributos_rodrigo, atributos_tuto, medio_influencia,
                expectativa_futuro, oportunidades_mercado, demanda_carrera, acceso_empleo_formal,
                prob_crisis_economia, prob_combustible, prob_transporte, prob_corrupcion,
                prob_seguridad, prob_salud_educacion, prob_medioambiente,
                trayectoria_influye, trayectoria_conocimiento, vp_importancia
            ) VALUES (
                %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s
            )
            """
            
            valores = (
                encuesta_id, hash_anonimo, ip_hash,
                data.get('edad'), data.get('genero'), data.get('departamento'),
                data.get('provincia'), data.get('situacion'),
                data.get('carrera_est') or data.get('carrera_prof'),
                data.get('area_prof'), data.get('estrato'),
                data.get('internet_diario'), data.get('estatus_laboral'), servicios,
                data.get('intencion_voto'), data.get('seguridad_voto'),
                data.get('evento_determinante'), data.get('evento_otro'),
                data.get('interes_politica'), data.get('frecuencia_conversacion'),
                data.get('alineamiento'),
                data.get('s3_economia'), data.get('s3_educacion'),
                data.get('s3_corrupcion_justicia'), data.get('s3_servicios'),
                data.get('s3_seguridad'), data.get('s3_medioambiente'),
                data.get('s3_derechos'), data.get('s3_modelo_desarrollo'),
                json.dumps(atributos_rodrigo), json.dumps(atributos_tuto), medios,
                data.get('expectativa_futuro'), data.get('cond_oportunidades'),
                data.get('cond_demanda_carrera'), data.get('cond_acceso_formal'),
                data.get('prob_crisis'), data.get('prob_combustible'),
                data.get('prob_transporte'), data.get('prob_corrupcion'),
                data.get('prob_seguridad'), data.get('prob_salud_educacion'),
                data.get('prob_medioambiente'),
                data.get('trayectoria_influye'), data.get('trayectoria_conocimiento'),
                data.get('vp_importancia')
            )
            
            cursor.execute(query, valores)
            conn.commit()
            
            print(f"✓ Respuesta insertada: {hash_anonimo[:16]}...")
            return True
            
    except Error as e:
        print(f"✗ Error al insertar respuesta: {e}")
        return False

def exportar_respuestas(encuesta_id: int, formato: str = 'csv', usuario: str = 'admin') -> Optional[str]:
    """
    Exporta respuestas en formato especificado
    
    Args:
        encuesta_id: ID de la encuesta
        formato: 'csv', 'excel' o 'json'
        usuario: Usuario que realiza la exportación
        
    Returns:
        Ruta del archivo generado
    """
    try:
        df = fetch_responses_df(encuesta_id, only_active=False)
        
        if df.empty:
            print("⚠ No hay datos para exportar")
            return None
        
        timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
        
        if formato == 'csv':
            filename = f'export_encuesta_{encuesta_id}_{timestamp}.csv'
            df.to_csv(filename, index=False, encoding='utf-8-sig')
        elif formato == 'excel':
            filename = f'export_encuesta_{encuesta_id}_{timestamp}.xlsx'
            df.to_excel(filename, index=False, engine='openpyxl')
        elif formato == 'json':
            filename = f'export_encuesta_{encuesta_id}_{timestamp}.json'
            df.to_json(filename, orient='records', indent=2, force_ascii=False)
        else:
            print(f"✗ Formato no soportado: {formato}")
            return None
        
        # Registrar exportación
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO exportaciones (encuesta_id, usuario, formato, num_registros)
                VALUES (%s, %s, %s, %s)
            """, (encuesta_id, usuario, formato, len(df)))
            conn.commit()
        
        print(f"✓ Datos exportados: {filename}")
        return filename
        
    except Exception as e:
        print(f"✗ Error al exportar: {e}")
        return None

# Compatibilidad con código existente
def load_from_excel(path: str, sheet_name: str = "Resultados Originales") -> pd.DataFrame:
    """Mantiene compatibilidad con código legacy que usa Excel"""
    df = pd.read_excel(path, sheet_name=sheet_name)
    return df