import os
import json
import time
import hashlib
from datetime import datetime
from src.extensions import db


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

class Encuesta(db.Model):
    __tablename__ = "encuestas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text)
    habilitada = db.Column(db.Boolean, default=True)
    fecha_inicio = db.Column(db.DateTime)
    fecha_fin = db.Column(db.DateTime)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Respuesta(db.Model):
    __tablename__ = "respuestas"

    id = db.Column(db.Integer, primary_key=True)
    encuesta_id = db.Column(db.Integer, db.ForeignKey("encuestas.id"), nullable=False)

    hash_anonimo = db.Column(db.String(64), nullable=False)
    ip_hash = db.Column(db.String(64))

    edad = db.Column(db.String(20))
    genero = db.Column(db.String(50))
    departamento = db.Column(db.String(50))
    provincia = db.Column(db.String(100))
    situacion_educativa = db.Column(db.String(50))
    carrera = db.Column(db.String(100))
    area_profesional = db.Column(db.String(100))
    estrato_socioeconomico = db.Column(db.String(50))
    tiempo_internet = db.Column(db.String(50))
    estatus_laboral = db.Column(db.String(100))
    servicios_basicos = db.Column(db.Text)

    intencion_voto = db.Column(db.String(100))
    seguridad_voto = db.Column(db.Integer)
    evento_determinante = db.Column(db.String(100))
    evento_otro = db.Column(db.Text)
    interes_politica = db.Column(db.Integer)
    frecuencia_conversacion = db.Column(db.Integer)
    alineamiento_ideologico = db.Column(db.String(50))

    factor_economia = db.Column(db.Integer)
    factor_educacion = db.Column(db.Integer)
    factor_corrupcion = db.Column(db.Integer)
    factor_servicios = db.Column(db.Integer)
    factor_seguridad = db.Column(db.Integer)
    factor_medioambiente = db.Column(db.Integer)
    factor_derechos = db.Column(db.Integer)
    factor_modelo_desarrollo = db.Column(db.Integer)

    atributos_rodrigo = db.Column(db.JSON)
    atributos_tuto = db.Column(db.JSON)
    medio_influencia = db.Column(db.Text)

    expectativa_futuro = db.Column(db.String(150))
    oportunidades_mercado = db.Column(db.String(50))
    demanda_carrera = db.Column(db.String(50))
    acceso_empleo_formal = db.Column(db.String(50))

    prob_crisis_economia = db.Column(db.Integer)
    prob_combustible = db.Column(db.Integer)
    prob_transporte = db.Column(db.Integer)
    prob_corrupcion = db.Column(db.Integer)
    prob_seguridad = db.Column(db.Integer)
    prob_salud_educacion = db.Column(db.Integer)
    prob_medioambiente = db.Column(db.Integer)

    trayectoria_influye = db.Column(db.Integer)
    trayectoria_conocimiento = db.Column(db.Integer)
    vp_importancia = db.Column(db.Integer)

    fecha_respuesta = db.Column(db.DateTime, default=datetime.utcnow)
    user_agent = db.Column(db.Text)

def save_form_to_db(form_dict, ip: str = "", user_agent: str = ""):
    """
    Guarda SOLO encuesta (paralelo a Sheets).
    form_dict: request.form.to_dict(flat=False)
    """
    def first(key, default=None):
        v = form_dict.get(key)
        if not v:
            return default
        return v[0] if isinstance(v, list) else v

    def as_list(key):
        v = form_dict.get(key)
        if not v:
            return []
        return v if isinstance(v, list) else [v]

    def to_int(x):
        try:
            return int(float(x))
        except Exception:
            return None

    encuesta_id = int(os.getenv("ENCUESTA_ID", "1"))
    salt = os.getenv("ANON_SALT", os.getenv("SECRET_KEY", "tss-salt"))
    ts = str(time.time())

    hash_anonimo = sha256_hex(f"{salt}|{ts}|{user_agent}")
    ip_hash = sha256_hex(f"{salt}|{ip}") if ip else None

    attrs_rodrigo = [to_int(first(f"attr_rodrigo_{k}")) for k in range(1, 11)]
    attrs_tuto = [to_int(first(f"attr_tuto_{k}")) for k in range(1, 11)]

    resp = Respuesta(
        encuesta_id=encuesta_id,
        hash_anonimo=hash_anonimo,
        ip_hash=ip_hash,

        edad=first("edad"),
        genero=first("genero"),
        departamento=first("departamento"),
        provincia=first("provincia"),
        situacion_educativa=first("situacion"),
        carrera=first("carrera_est") or first("carrera_prof"),
        area_profesional=first("area_prof"),
        estrato_socioeconomico=first("estrato"),
        tiempo_internet=first("internet_diario"),
        estatus_laboral=first("estatus_laboral"),
        servicios_basicos=json.dumps(as_list("servicios"), ensure_ascii=False),

        intencion_voto=first("intencion_voto"),
        seguridad_voto=to_int(first("seguridad_voto")),
        evento_determinante=first("evento_determinante"),
        evento_otro=first("evento_otro"),
        interes_politica=to_int(first("interes_politica")),
        frecuencia_conversacion=to_int(first("frecuencia_conversacion")),
        alineamiento_ideologico=first("alineamiento"),

        factor_economia=to_int(first("s3_economia")),
        factor_educacion=to_int(first("s3_educacion")),
        factor_corrupcion=to_int(first("s3_corrupcion_justicia")),
        factor_servicios=to_int(first("s3_servicios")),
        factor_seguridad=to_int(first("s3_seguridad")),
        factor_medioambiente=to_int(first("s3_medioambiente")),
        factor_derechos=to_int(first("s3_derechos")),
        factor_modelo_desarrollo=to_int(first("s3_modelo_desarrollo")),

        atributos_rodrigo=attrs_rodrigo,
        atributos_tuto=attrs_tuto,
        medio_influencia=json.dumps(as_list("medio_influencia"), ensure_ascii=False),

        expectativa_futuro=first("expectativa_futuro"),
        oportunidades_mercado=first("cond_oportunidades"),
        demanda_carrera=first("cond_demanda_carrera"),
        acceso_empleo_formal=first("cond_acceso_formal"),

        prob_crisis_economia=to_int(first("prob_crisis")),
        prob_combustible=to_int(first("prob_combustible")),
        prob_transporte=to_int(first("prob_transporte")),
        prob_corrupcion=to_int(first("prob_corrupcion")),
        prob_seguridad=to_int(first("prob_seguridad")),
        prob_salud_educacion=to_int(first("prob_salud_educacion")),
        prob_medioambiente=to_int(first("prob_medioambiente")),

        trayectoria_influye=to_int(first("trayectoria_influye")),
        trayectoria_conocimiento=to_int(first("trayectoria_conocimiento")),
        vp_importancia=to_int(first("vp_importancia")),

        user_agent=user_agent
    )

    db.session.add(resp)
    db.session.commit()
