-- ============================================================
-- INSERCIÓN DE DATOS DE ENCUESTA
-- Sistema de Encuestas Electorales TSS
-- ============================================================

USE elecciones_tss;

-- Deshabilitar verificaciones temporalmente para mejor rendimiento
SET foreign_key_checks = 0;
SET unique_checks = 0;
SET autocommit = 0;

-- ============================================================
-- INSERCIÓN DE RESPUESTAS (50 registros)
-- ============================================================

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
    trayectoria_influye, trayectoria_conocimiento, vp_importancia,
    fecha_respuesta
) VALUES
-- Registro 1
(1, SHA2(CONCAT('2025-10-06 8:00:00', UUID()), 256), SHA2('192.168.1.1', 256),
'18-24', 'Masculino', 'Cochabamba', 'Cochabamba (Cercado)', 'estudiante',
'Ing. Electrónica', 'Administración/Economía', 'Medio-Bajo',
'7 h o más', 'Empleado Institución Pública', '["Agua Potable", "Energía Eléctrica"]',
'Aún no lo decido', 3, 'Denuncia', NULL,
3, 2, 'Centro-Derecha',
4, 4, 3, 2, 3, 5, 2, 3,
'[2,2,2,3,3,4,5,5,2,2]', '[2,4,5,5,2,3,3,4,3,3]', '["Blogs/Revistas digitales", "YouTube (análisis político)", "Instagram"]',
'Conseguir un empleo estable en mi área profesional.', 'Muchas', 'Muy demandada', 'Difícil de obtener',
3, 4, 4, 4, 4, 2, 2, 4, 4, 4,
'2025-10-06 08:00:00'),

-- Registro 2
(1, SHA2(CONCAT('2025-10-06 8:52:00', UUID()), 256), SHA2('192.168.1.2', 256),
'18-24', 'Femenino', 'Cochabamba', 'Tiquipaya', 'estudiante',
'Ing. Eléctrica', 'Administración/Economía', 'Medio-Bajo',
'5-6 h', 'Freelance', '["Agua Potable", "Saneamiento", "Internet"]',
'Rodrigo Paz Pereira (Izquierda)', 1, 'Denuncia', NULL,
2, 4, 'Izquierda/Progresista',
2, 2, 5, 4, 3, 3, 5, 4,
'[2,3,5,5,5,5,3,3,4,5]', '[3,4,3,2,5,5,4,5,5,4]', '["Familiares", "Periódico", "Tiktok", "LinkedIn"]',
'Aún no lo sé.', 'Nada', 'Muy demandada', 'Muy accesible',
2, 5, 3, 3, 3, 2, 5, 2, 2, 3,
'2025-10-06 08:52:00'),

-- Registro 3
(1, SHA2(CONCAT('2025-10-06 9:24:00', UUID()), 256), SHA2('192.168.1.3', 256),
'18-24', 'Femenino', 'Cochabamba', 'Quillacollo', 'estudiante',
'Ing. Ambiental', 'Ingenierías', 'Bajo',
'1-2 h', 'Desempleado', '["Saneamiento", "Internet"]',
'Aún no lo decido', 5, 'Ninguno', NULL,
5, 2, 'Derecha Conservadora',
2, 3, 3, 4, 5, 5, 3, 3,
'[4,5,4,4,4,3,4,5,4,3]', '[2,5,4,3,4,3,4,3,2,5]', '["X", "Periódico", "Familiares"]',
'Crear mi propio emprendimiento.', 'Bastantes', 'Medianamente demandada', 'Accesible',
4, 5, 5, 2, 4, 4, 5, 5, 4, 4,
'2025-10-06 09:24:00'),

-- Registro 4
(1, SHA2(CONCAT('2025-10-06 10:45:00', UUID()), 256), SHA2('192.168.1.4', 256),
'18-24', 'Masculino', 'Cochabamba', 'Colcapirhua', 'estudiante',
'Derecho', 'Ingenierías', 'Medio',
'1-2 h', 'Innovador', '["Saneamiento", "Agua Potable", "Internet"]',
'Rodrigo Paz Pereira (Izquierda)', 5, 'Debate', NULL,
1, 1, 'Centro-Izquierda',
4, 2, 2, 2, 5, 3, 3, 3,
'[5,4,5,5,4,3,3,4,4,4]', '[5,3,4,2,5,2,4,5,2,4]', '["X", "Instagram", "YouTube (análisis político)", "Docentes/Mentores"]',
'Conseguir un empleo estable en mi área profesional.', 'Muchas', 'Medianamente demandada', 'Muy difícil de obtener',
5, 2, 4, 4, 2, 5, 3, 5, 2, 5,
'2025-10-06 10:45:00'),

-- Registro 5
(1, SHA2(CONCAT('2025-10-06 11:51:00', UUID()), 256), SHA2('192.168.1.5', 256),
'18-24', 'Masculino', 'Cochabamba', 'Cochabamba (Cercado)', 'estudiante',
'Ing. Civil', 'Ingenierías', 'Medio-Bajo',
'1-2 h', 'Innovador', '["Energía Eléctrica", "Agua Potable"]',
'Jorge Quiroga Ramírez (Derecha)', 4, 'Debate', NULL,
4, 4, 'Izquierda/Progresista',
3, 3, 4, 2, 3, 3, 2, 3,
'[5,4,5,4,3,5,5,3,3,3]', '[4,3,4,2,5,2,2,3,5,4]', '["X", "Periódico"]',
'Conseguir un empleo estable en mi área profesional.', 'Algunas', 'Demandada', 'Difícil de obtener',
4, 4, 3, 2, 5, 3, 4, 5, 4, 4,
'2025-10-06 11:51:00'),

-- Registro 6
(1, SHA2(CONCAT('2025-10-06 13:06:00', UUID()), 256), SHA2('192.168.1.6', 256),
'18-24', 'Masculino', 'Cochabamba', 'Sacaba', 'profesional',
'Ing. Eléctrica', 'Ingenierías', 'Bajo',
'7 h o más', 'Empleado Institución Pública', '["Energía Eléctrica", "Saneamiento"]',
'Aún no lo decido', 1, 'Debate', NULL,
1, 4, 'Centro',
4, 5, 3, 4, 2, 4, 5, 3,
'[3,4,3,5,5,2,3,5,2,4]', '[5,4,5,2,2,5,4,4,3,5]', '["Periódico", "Facebook", "Prensa en línea", "YouTube (análisis político)"]',
'Conseguir un empleo estable en mi área profesional.', 'Muchas', 'Muy demandada', 'Muy accesible',
3, 3, 4, 4, 3, 3, 2, 3, 4, 5,
'2025-10-06 13:06:00'),

-- Registro 7
(1, SHA2(CONCAT('2025-10-06 13:20:00', UUID()), 256), SHA2('192.168.1.7', 256),
'31-40', 'Masculino', 'Cochabamba', 'Tiquipaya', 'profesional',
'Psicología', 'Otro', 'Medio-Bajo',
'3-4 h', 'Empleado Empresa Privada', '["Energía Eléctrica", "Agua Potable", "Internet", "Saneamiento"]',
'Jorge Quiroga Ramírez (Derecha)', 5, 'Debate', NULL,
3, 1, 'Centro',
4, 4, 5, 4, 3, 2, 5, 2,
'[5,3,4,2,4,3,4,3,2,4]', '[5,3,4,4,2,3,2,3,2,4]', '["Blogs/Revistas digitales", "Instagram", "WhatsApp"]',
'Continuar estudios de posgrado o especialización.', 'Pocas', 'Demandada', 'Accesible',
5, 3, 2, 5, 2, 4, 4, 5, 4, 5,
'2025-10-06 13:20:00'),

-- Registro 8
(1, SHA2(CONCAT('2025-10-06 16:40:00', UUID()), 256), SHA2('192.168.1.8', 256),
'25-30', 'Femenino', 'Cochabamba', 'Quillacollo', 'profesional',
'Ing. Eléctrica', 'Administración/Economía', 'Medio',
'5-6 h', 'Empleado Empresa Privada', '["Agua Potable", "Internet"]',
'Rodrigo Paz Pereira (Izquierda)', 1, 'Denuncia', NULL,
2, 3, 'Izquierda/Progresista',
3, 5, 4, 2, 2, 5, 5, 3,
'[5,2,2,4,3,4,3,3,3,2]', '[5,2,4,4,5,5,4,4,3,3]', '["X", "WhatsApp", "LinkedIn"]',
'Aún no lo sé.', 'Muchas', 'Demandada', 'Accesible',
4, 3, 5, 2, 2, 2, 2, 5, 4, 3,
'2025-10-06 16:40:00'),

-- Registro 9
(1, SHA2(CONCAT('2025-10-06 17:20:00', UUID()), 256), SHA2('192.168.1.9', 256),
'25-30', 'Masculino', 'Cochabamba', 'Sacaba', 'profesional',
'Ing. Ambiental', 'Otro', 'Bajo',
'7 h o más', 'Freelance', '["Energía Eléctrica", "Internet", "Saneamiento", "Agua Potable"]',
'Rodrigo Paz Pereira (Izquierda)', 5, 'Denuncia', NULL,
1, 3, 'Centro',
4, 3, 3, 2, 5, 4, 5, 4,
'[2,4,2,5,5,3,5,5,2,2]', '[5,3,2,3,4,3,3,2,3,4]', '["WhatsApp", "Tiktok", "LinkedIn", "X"]',
'Conseguir un empleo estable en mi área profesional.', 'Pocas', 'Poco demandada', 'Medianamente accesible',
5, 2, 4, 5, 2, 2, 2, 2, 3, 2,
'2025-10-06 17:20:00'),

-- Registro 10
(1, SHA2(CONCAT('2025-10-06 19:28:00', UUID()), 256), SHA2('192.168.1.10', 256),
'31-40', 'Masculino', 'Cochabamba', 'Cochabamba (Cercado)', 'estudiante',
'Ing. Industrial', 'Ingenierías', 'Medio',
'1-2 h', 'Empleado Institución Pública', '["Agua Potable", "Energía Eléctrica"]',
'Jorge Quiroga Ramírez (Derecha)', 2, 'Denuncia', NULL,
2, 2, 'Centro',
5, 4, 4, 3, 4, 3, 4, 4,
'[4,3,4,4,4,5,3,3,5,5]', '[3,4,2,3,5,3,5,4,2,4]', '["Televisión tradicional", "Radio tradicional"]',
'Aún no lo sé.', 'Pocas', 'Demandada', 'Medianamente accesible',
2, 4, 5, 5, 2, 3, 3, 2, 5, 5,
'2025-10-06 19:28:00');

-- Continuación de registros 11-20
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
    trayectoria_influye, trayectoria_conocimiento, vp_importancia,
    fecha_respuesta
) VALUES
-- Registro 11
(1, SHA2(CONCAT('2025-10-06 20:24:00', UUID()), 256), SHA2('192.168.1.11', 256),
'18-24', 'Masculino', 'Cochabamba', 'Cochabamba (Cercado)', 'estudiante',
'Ing. Mecánica', 'Ingenierías', 'Medio-Bajo',
'3-4 h', 'Empleado Empresa Privada', '["Agua Potable", "Internet", "Energía Eléctrica"]',
'Aún no lo decido', 1, 'Denuncia', NULL,
5, 2, 'Centro-Izquierda',
2, 2, 4, 4, 5, 4, 4, 2,
'[3,4,3,2,5,3,3,3,5,5]', '[5,3,3,2,3,4,4,3,3,3]', '["Facebook", "Prensa en línea", "Instagram", "Televisión tradicional"]',
'Crear mi propio emprendimiento.', 'Algunas', 'Medianamente demandada', 'Muy difícil de obtener',
5, 4, 5, 5, 4, 2, 4, 4, 3, 4,
'2025-10-06 20:24:00'),

-- Registro 12
(1, SHA2(CONCAT('2025-10-06 21:40:00', UUID()), 256), SHA2('192.168.1.12', 256),
'18-24', 'Femenino', 'Cochabamba', 'Vinto', 'estudiante',
'Ing. de Sistemas', 'Ingenierías', 'Medio',
'5-6 h', 'Innovador', '["Agua Potable", "Internet", "Energía Eléctrica", "Saneamiento"]',
'Jorge Quiroga Ramírez (Derecha)', 4, 'Plan Económico', NULL,
1, 3, 'Centro',
2, 4, 3, 4, 3, 4, 5, 5,
'[5,2,5,5,4,4,3,3,2,3]', '[2,3,3,5,4,2,4,3,5,2]', '["Tiktok", "Amigos", "Radio tradicional"]',
'Aún no lo sé.', 'Nada', 'Nada demandada', 'Muy difícil de obtener',
3, 4, 3, 3, 2, 3, 4, 5, 4, 3,
'2025-10-06 21:40:00'),

-- Registro 13
(1, SHA2(CONCAT('2025-10-06 22:24:00', UUID()), 256), SHA2('192.168.1.13', 256),
'18-24', 'Femenino', 'Cochabamba', 'Sacaba', 'estudiante',
'Ing. de Sistemas', 'Ingenierías', 'Bajo',
'7 h o más', 'Emprendedor', '["Agua Potable", "Saneamiento", "Internet", "Energía Eléctrica"]',
'Jorge Quiroga Ramírez (Derecha)', 4, 'Debate', NULL,
4, 2, 'Centro-Izquierda',
3, 2, 4, 3, 5, 2, 4, 5,
'[3,3,3,4,2,4,2,3,3,2]', '[4,2,4,2,3,2,5,4,5,5]', '["Periódico", "Compañeros", "YouTube (análisis político)"]',
'Crear mi propio emprendimiento.', 'Algunas', 'Poco demandada', 'Medianamente accesible',
5, 3, 4, 3, 2, 5, 3, 3, 4, 4,
'2025-10-06 22:24:00'),

-- Registro 14
(1, SHA2(CONCAT('2025-10-06 23:43:00', UUID()), 256), SHA2('192.168.1.14', 256),
'18-24', 'Masculino', 'Cochabamba', 'Sacaba', 'estudiante',
'Ing. Industrial', 'Ingenierías', 'Medio',
'5-6 h', 'Freelance', '["Agua Potable", "Saneamiento"]',
'Jorge Quiroga Ramírez (Derecha)', 2, 'Plan Económico', NULL,
3, 3, 'Centro-Izquierda',
2, 5, 2, 2, 2, 3, 3, 2,
'[5,2,4,2,3,2,3,5,2,5]', '[2,3,2,4,3,2,2,5,3,3]', '["Blogs/Revistas digitales", "LinkedIn", "Radio tradicional", "Televisión tradicional"]',
'Crear mi propio emprendimiento.', 'Pocas', 'Medianamente demandada', 'Medianamente accesible',
2, 3, 2, 3, 2, 2, 5, 5, 3, 5,
'2025-10-06 23:43:00'),

-- Registro 15
(1, SHA2(CONCAT('2025-10-06 23:45:00', UUID()), 256), SHA2('192.168.1.15', 256),
'25-30', 'Femenino', 'Cochabamba', 'Cochabamba (Cercado)', 'estudiante',
'Ing. Civil', 'Ingenierías', 'Bajo',
'5-6 h', 'Innovador', '["Saneamiento", "Agua Potable"]',
'Jorge Quiroga Ramírez (Derecha)', 4, 'Otro (Especificar)', 'Crisis económica grave',
1, 3, 'Derecha Conservadora',
3, 5, 3, 4, 2, 5, 5, 3,
'[3,5,4,3,5,3,4,2,5,2]', '[4,2,5,2,4,2,5,2,5,2]', '["Prensa en línea", "Facebook", "Radio tradicional"]',
'Continuar estudios de posgrado o especialización.', 'Bastantes', 'Poco demandada', 'Muy difícil de obtener',
4, 3, 5, 3, 5, 3, 2, 3, 5, 3,
'2025-10-06 23:45:00'),

-- Registro 16
(1, SHA2(CONCAT('2025-10-07 00:08:00', UUID()), 256), SHA2('192.168.1.16', 256),
'18-24', 'Femenino', 'Cochabamba', 'Quillacollo', 'profesional',
'Administración de Empresas', 'Ingenierías', 'Bajo',
'7 h o más', 'Innovador', '["Agua Potable", "Internet", "Energía Eléctrica", "Saneamiento"]',
'Jorge Quiroga Ramírez (Derecha)', 3, 'Ninguno', NULL,
1, 2, 'Centro',
4, 2, 4, 4, 2, 2, 5, 3,
'[3,3,2,4,3,4,3,3,2,2]', '[2,4,5,3,3,5,2,4,4,3]', '["Radio tradicional", "Facebook", "Familiares", "Tiktok"]',
'Continuar estudios de posgrado o especialización.', 'Muchas', 'Poco demandada', 'Medianamente accesible',
5, 2, 4, 2, 2, 5, 2, 4, 2, 3,
'2025-10-07 00:08:00'),

-- Registro 17
(1, SHA2(CONCAT('2025-10-07 00:57:00', UUID()), 256), SHA2('192.168.1.17', 256),
'25-30', 'Masculino', 'Cochabamba', 'Cochabamba (Cercado)', 'estudiante',
'Ing. Electrónica', 'Ingenierías', 'Bajo',
'3-4 h', 'Innovador', '["Energía Eléctrica", "Agua Potable", "Internet"]',
'Rodrigo Paz Pereira (Izquierda)', 3, 'Debate', NULL,
2, 1, 'Izquierda/Progresista',
5, 5, 2, 5, 2, 2, 5, 4,
'[5,4,4,2,5,5,4,3,5,2]', '[5,3,2,5,5,5,4,2,5,3]', '["Instagram", "Tiktok", "X", "WhatsApp"]',
'Trabajar en el extranjero.', 'Nada', 'Nada demandada', 'Difícil de obtener',
5, 3, 3, 4, 4, 3, 5, 5, 2, 4,
'2025-10-07 00:57:00'),

-- Registro 18
(1, SHA2(CONCAT('2025-10-07 02:24:00', UUID()), 256), SHA2('192.168.1.18', 256),
'18-24', 'Masculino', 'Cochabamba', 'Cochabamba (Cercado)', 'estudiante',
'Administración de Empresas', 'Educación', 'Bajo',
'5-6 h', 'Empleado Empresa Privada', '["Agua Potable", "Saneamiento", "Energía Eléctrica", "Internet"]',
'Voto Blanco', 4, 'Debate', NULL,
5, 3, 'Derecha Conservadora',
3, 2, 3, 4, 4, 4, 3, 2,
'[3,2,5,5,4,4,5,2,2,3]', '[3,3,4,3,4,5,4,4,5,5]', '["LinkedIn", "Blogs/Revistas digitales"]',
'Conseguir un empleo estable en mi área profesional.', 'Bastantes', 'Nada demandada', 'Difícil de obtener',
2, 2, 2, 4, 4, 5, 2, 5, 3, 2,
'2025-10-07 02:24:00'),

-- Registro 19
(1, SHA2(CONCAT('2025-10-07 03:38:00', UUID()), 256), SHA2('192.168.1.19', 256),
'25-30', 'Masculino', 'Cochabamba', 'Sacaba', 'estudiante',
'Ing. Electrónica', 'Otro', 'Medio-Alto',
'3-4 h', 'Freelance', '["Saneamiento", "Internet", "Agua Potable"]',
'Jorge Quiroga Ramírez (Derecha)', 1, 'Ninguno', NULL,
4, 4, 'Centro',
3, 4, 4, 4, 3, 4, 3, 4,
'[4,4,5,2,3,3,2,4,2,5]', '[2,4,3,3,2,3,2,5,4,4]', '["X", "Amigos", "Familiares"]',
'Crear mi propio emprendimiento.', 'Bastantes', 'Medianamente demandada', 'Muy difícil de obtener',
4, 5, 5, 2, 5, 2, 5, 5, 4, 2,
'2025-10-07 03:38:00'),

-- Registro 20
(1, SHA2(CONCAT('2025-10-07 05:40:00', UUID()), 256), SHA2('192.168.1.20', 256),
'18-24', 'Femenino', 'Cochabamba', 'Tiquipaya', 'estudiante',
'Ing. Informática', 'Ingenierías', 'Medio-Bajo',
'3-4 h', 'Empleado Empresa Privada', '["Saneamiento", "Energía Eléctrica", "Agua Potable"]',
'Voto Nulo', 5, 'Denuncia', NULL,
3, 4, 'Derecha Conservadora',
2, 3, 4, 4, 2, 5, 5, 3,
'[4,4,5,2,5,3,3,5,5,5]', '[4,2,4,3,4,4,4,3,4,2]', '["WhatsApp", "Televisión tradicional", "Periódico"]',
'Conseguir un empleo estable en mi área profesional.', 'Bastantes', 'Medianamente demandada', 'Muy difícil de obtener',
3, 4, 2, 2, 5, 4, 3, 3, 4, 3,
'2025-10-07 05:40:00');