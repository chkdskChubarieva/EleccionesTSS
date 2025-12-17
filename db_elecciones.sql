-- ============================================================
-- SISTEMA DE GESTIÓN DE ENCUESTAS ELECTORALES
-- Base de datos con capacidad de anonimización
-- Compatible con phpMyAdmin
-- ============================================================

-- Crear base de datos
CREATE DATABASE IF NOT EXISTS elecciones_tss 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE elecciones_tss;

-- ============================================================
-- 1. TABLA DE ENCUESTAS (Gestión y Control)
-- ============================================================
CREATE TABLE encuestas (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    habilitada BOOLEAN DEFAULT TRUE,
    fecha_inicio DATETIME,
    fecha_fin DATETIME,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_habilitada (habilitada),
    INDEX idx_fechas (fecha_inicio, fecha_fin)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 2. TABLA PRINCIPAL DE RESPUESTAS (Anonimizada)
-- ============================================================
CREATE TABLE respuestas (
    id INT PRIMARY KEY AUTO_INCREMENT,
    encuesta_id INT NOT NULL,
    
    -- Anonimización
    hash_anonimo VARCHAR(64) NOT NULL COMMENT 'Hash único del respondiente',
    ip_hash VARCHAR(64) COMMENT 'IP hasheada para evitar duplicados',
    
    -- SECCIÓN 1: Datos Demográficos
    edad VARCHAR(20),
    genero VARCHAR(50),
    departamento VARCHAR(50),
    provincia VARCHAR(100),
    situacion_educativa VARCHAR(50),
    carrera VARCHAR(100),
    area_profesional VARCHAR(100),
    estrato_socioeconomico VARCHAR(50),
    tiempo_internet VARCHAR(50),
    estatus_laboral VARCHAR(100),
    servicios_basicos TEXT COMMENT 'JSON array de servicios',
    
    -- SECCIÓN 2: Intención de Voto
    intencion_voto VARCHAR(100),
    seguridad_voto TINYINT COMMENT '1-5',
    evento_determinante VARCHAR(100),
    evento_otro TEXT,
    interes_politica TINYINT COMMENT '1-5',
    frecuencia_conversacion TINYINT COMMENT '1-4',
    alineamiento_ideologico VARCHAR(50),
    
    -- SECCIÓN 3: Factores de Decisión (Escala 1-5)
    factor_economia TINYINT,
    factor_educacion TINYINT,
    factor_corrupcion TINYINT,
    factor_servicios TINYINT,
    factor_seguridad TINYINT,
    factor_medioambiente TINYINT,
    factor_derechos TINYINT,
    factor_modelo_desarrollo TINYINT,
    
    -- SECCIÓN 4: Atributos Candidatos (JSON)
    atributos_rodrigo JSON COMMENT 'Array de 10 valores 1-5',
    atributos_tuto JSON COMMENT 'Array de 10 valores 1-5',
    medio_influencia TEXT COMMENT 'Array de medios seleccionados',
    
    -- SECCIÓN 5: Expectativas Laborales
    expectativa_futuro VARCHAR(150),
    oportunidades_mercado VARCHAR(50),
    demanda_carrera VARCHAR(50),
    acceso_empleo_formal VARCHAR(50),
    
    -- SECCIÓN 6: Problemáticas (Escala 1-5)
    prob_crisis_economia TINYINT,
    prob_combustible TINYINT,
    prob_transporte TINYINT,
    prob_corrupcion TINYINT,
    prob_seguridad TINYINT,
    prob_salud_educacion TINYINT,
    prob_medioambiente TINYINT,
    
    -- SECCIÓN 7: Trayectoria Candidatos
    trayectoria_influye TINYINT COMMENT '1-5',
    trayectoria_conocimiento TINYINT COMMENT '1-5',
    vp_importancia TINYINT COMMENT '1-5',
    
    -- Metadatos
    fecha_respuesta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,
    
    FOREIGN KEY (encuesta_id) REFERENCES encuestas(id) ON DELETE CASCADE,
    INDEX idx_fecha (fecha_respuesta),
    INDEX idx_encuesta (encuesta_id),
    INDEX idx_hash (hash_anonimo),
    INDEX idx_intencion (intencion_voto),
    INDEX idx_departamento (departamento),
    INDEX idx_estrato (estrato_socioeconomico)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 3. TABLA DE EXPORTACIONES (Auditoría)
-- ============================================================
CREATE TABLE exportaciones (
    id INT PRIMARY KEY AUTO_INCREMENT,
    encuesta_id INT,
    usuario VARCHAR(100) NOT NULL,
    formato VARCHAR(20) NOT NULL COMMENT 'csv, excel, json',
    num_registros INT NOT NULL,
    filtros_aplicados TEXT,
    fecha_exportacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (encuesta_id) REFERENCES encuestas(id) ON DELETE SET NULL,
    INDEX idx_fecha (fecha_exportacion),
    INDEX idx_usuario (usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 4. TABLA DE LOGS DE SISTEMA (Seguridad)
-- ============================================================
CREATE TABLE logs_sistema (
    id INT PRIMARY KEY AUTO_INCREMENT,
    evento VARCHAR(100) NOT NULL,
    descripcion TEXT,
    usuario VARCHAR(100),
    ip_hash VARCHAR(64),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_evento (evento),
    INDEX idx_fecha (fecha)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- DATOS INICIALES
-- ============================================================

-- Insertar encuesta activa
INSERT INTO encuestas (nombre, descripcion, habilitada, fecha_inicio) 
VALUES (
    'Encuesta Intención de Voto 2025 - Segunda Vuelta',
    'Encuesta sobre percepciones y preferencias electorales en jóvenes universitarios de Bolivia',
    TRUE,
    NOW()
);

-- ============================================================
-- VISTAS ÚTILES PARA ANÁLISIS
-- ============================================================

-- Vista de distribución de votos
CREATE VIEW v_distribucion_votos AS
SELECT 
    e.nombre AS encuesta,
    r.intencion_voto,
    COUNT(*) as total,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM respuestas WHERE encuesta_id = r.encuesta_id), 2) as porcentaje
FROM respuestas r
JOIN encuestas e ON r.encuesta_id = e.id
WHERE r.intencion_voto IS NOT NULL
GROUP BY e.nombre, r.intencion_voto
ORDER BY total DESC;

-- Vista por departamento
CREATE VIEW v_votos_por_departamento AS
SELECT 
    departamento,
    intencion_voto,
    COUNT(*) as total
FROM respuestas
WHERE intencion_voto IS NOT NULL 
  AND departamento IS NOT NULL
GROUP BY departamento, intencion_voto
ORDER BY departamento, total DESC;

-- Vista por estrato socioeconómico
CREATE VIEW v_votos_por_estrato AS
SELECT 
    estrato_socioeconomico,
    intencion_voto,
    COUNT(*) as total,
    AVG(seguridad_voto) as promedio_seguridad
FROM respuestas
WHERE intencion_voto IS NOT NULL 
  AND estrato_socioeconomico IS NOT NULL
GROUP BY estrato_socioeconomico, intencion_voto
ORDER BY estrato_socioeconomico, total DESC;

-- ============================================================
-- PROCEDIMIENTOS ALMACENADOS ÚTILES
-- ============================================================

DELIMITER //

-- Procedimiento para deshabilitar encuesta
CREATE PROCEDURE sp_deshabilitar_encuesta(IN p_encuesta_id INT)
BEGIN
    UPDATE encuestas 
    SET habilitada = FALSE,
        fecha_fin = NOW()
    WHERE id = p_encuesta_id;
    
    INSERT INTO logs_sistema (evento, descripcion) 
    VALUES ('ENCUESTA_DESHABILITADA', CONCAT('Encuesta ID: ', p_encuesta_id));
END //

-- Procedimiento para habilitar encuesta
CREATE PROCEDURE sp_habilitar_encuesta(IN p_encuesta_id INT)
BEGIN
    UPDATE encuestas 
    SET habilitada = TRUE,
        fecha_inicio = NOW(),
        fecha_fin = NULL
    WHERE id = p_encuesta_id;
    
    INSERT INTO logs_sistema (evento, descripcion) 
    VALUES ('ENCUESTA_HABILITADA', CONCAT('Encuesta ID: ', p_encuesta_id));
END //

-- Función para generar hash anónimo
CREATE FUNCTION fn_generar_hash(p_timestamp VARCHAR(50), p_random VARCHAR(50))
RETURNS VARCHAR(64)
DETERMINISTIC
BEGIN
    RETURN SHA2(CONCAT(p_timestamp, '-', p_random, '-', UUID()), 256);
END //

DELIMITER ;

-- ============================================================
-- ÍNDICES ADICIONALES PARA OPTIMIZACIÓN
-- ============================================================

-- Índices compuestos para consultas comunes
CREATE INDEX idx_voto_estrato ON respuestas(intencion_voto, estrato_socioeconomico);
CREATE INDEX idx_voto_depto ON respuestas(intencion_voto, departamento);
CREATE INDEX idx_fecha_encuesta ON respuestas(fecha_respuesta, encuesta_id);

-- ============================================================
-- PERMISOS Y SEGURIDAD (Opcional - ajustar según necesidad)
-- ============================================================

-- Crear usuario de solo lectura para análisis
-- CREATE USER 'analista_encuestas'@'localhost' IDENTIFIED BY 'password_seguro';
-- GRANT SELECT ON elecciones_tss.respuestas TO 'analista_encuestas'@'localhost';
-- GRANT SELECT ON elecciones_tss.v_* TO 'analista_encuestas'@'localhost';

-- ============================================================
-- VERIFICACIÓN FINAL
-- ============================================================

SELECT 'Base de datos creada exitosamente' AS Status;
SELECT COUNT(*) as Total_Tablas FROM information_schema.tables 
WHERE table_schema = 'elecciones_tss';

SHOW TABLES;