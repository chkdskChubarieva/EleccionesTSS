"""
Servicio de acceso a datos con MySQL
Reemplaza la lectura de Google Sheets
"""
import pandas as pd
from typing import Optional, List, Dict
from mysql.connector import Error
import sys
import os

# Agregar path para importar configuración
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from controllers.database import get_db_connection

# Mapeo de valores de voto
MAP_VOTO = {
    "Jorge Quiroga Ramírez (Derecha)": "A",
    "Rodrigo Paz Pereira (Izquierda)": "B",
    "Voto Blanco": "Blanco",
    "Voto Nulo": "Nulo",
    "Aún no lo decido": "Indeciso",
}

def fetch_responses_df(encuesta_id: int = 1, only_active: bool = True) -> pd.DataFrame:
    """
    Obtiene respuestas de la encuesta desde MySQL
    
    Args:
        encuesta_id: ID de la encuesta a consultar
        only_active: Solo incluir encuestas habilitadas
        
    Returns:
        DataFrame con todas las respuestas
    """
    try:
        with get_db_connection() as conn:
            # Query base
            query = """
            SELECT 
                r.*,
                e.nombre as encuesta_nombre,
                e.habilitada as encuesta_activa
            FROM respuestas r
            JOIN encuestas e ON r.encuesta_id = e.id
            WHERE r.encuesta_id = %s
            """
            
            if only_active:
                query += " AND e.habilitada = TRUE"
            
            query += " ORDER BY r.fecha_respuesta DESC"
            
            df = pd.read_sql(query, conn, params=(encuesta_id,))
            
            print(f"✓ Cargadas {len(df)} respuestas desde MySQL")
            return df
            
    except Error as e:
        print(f"✗ Error al obtener respuestas: {e}")
        return pd.DataFrame()

def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza el DataFrame para compatibilidad con el motor de simulación
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # 1. Estado inicial de voto
    if 'intencion_voto' in df.columns:
        df['estado_inicial'] = df['intencion_voto'].map(MAP_VOTO).fillna("Indeciso")
    else:
        df['estado_inicial'] = "Indeciso"
    
    # 2. Seguridad del voto (ya está como 1-5)
    if 'seguridad_voto' in df.columns:
        df['seguridad_1a5'] = pd.to_numeric(df['seguridad_voto'], errors='coerce').fillna(3).clip(1, 5)
    else:
        df['seguridad_1a5'] = 3
    
    # 3. Estrato socioeconómico
    df['estrato'] = df.get('estrato_socioeconomico', 'Medio').fillna('Medio').astype(str)
    
    # 4. Ideología
    df['ideologia'] = df.get('alineamiento_ideologico', 'Centro').fillna('Centro').astype(str)
    
    # 5. Evento determinante
    df['evento_det'] = df.get('evento_determinante', 'Ninguno').fillna('Ninguno').astype(str)
    
    # 6. Medios de comunicación
    df['medios'] = df.get('medio_influencia', '').fillna('').astype(str)
    
    # 7. ID de agente
    df['agent_id'] = range(1, len(df) + 1)
    
    # 8. Demografía adicional
    df['edad_rango'] = df.get('edad', '18-24')
    df['genero'] = df.get('genero', 'Prefiero no decir')
    df['departamento'] = df.get('departamento', 'No especificado')
    
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