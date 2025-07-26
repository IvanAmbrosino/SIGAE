SELECT
    -- Campos de la actividad
    act.id AS activity_id,
    act.satellite_id,
    act.orbit_number,
    act.start_time,
    act.max_elevation_time,
    act.max_elevation,
    act.end_time,
    act.duration,
    act.status AS activity_status,
    act.priority,
    -- Campos de la asignacion
    aa.id AS task_id,
    aa.antenna_id,
    aa.is_confirmed,
    aa.assigned_at,
    aa.confirmed_at,
    -- Campos de la Antena
    ant.name AS antenna_name,
    ant.code AS antenna_code,
    -- Campos del Satelite
    sat.name AS satellite_name,
    -- Campos de la configuracion de actividad
    ac.config_number AS config_number,
    act.updated_at,
    aa.last_sent_at,
    aa.send_status,
    aa.is_active
FROM activities act
JOIN activity_assignments aa ON act.id = aa.activity_id -- El primer filtro es si tiene una asignacion
JOIN antennas ant ON aa.antenna_id = ant.id             -- Obtenemos los datos de la antena
JOIN satellites sat ON act.satellite_id = sat.id        -- Obtenemos los datos del satellite
LEFT JOIN activity_configuration ac ON (                -- Obtenemos la configuracion de actividad si existe
    ac.satellite_id = act.satellite_id 
    AND ac.antenna_id = aa.antenna_id
    AND ac.is_active = TRUE                             -- Buscamos solo la activa
)
WHERE 
    -- Filtro por ventana de tiempo relevante
    act.end_time < NOW() + INTERVAL '72 hour'
    AND act.start_time > NOW() - INTERVAL '3 year'
    -- Filtro de estado de la actividad y asignacion
    AND (act.status = 'canceled' and aa.send_status IN ('confirmed') and aa.is_active = TRUE)
    OR (act.status IN ('authorized') AND aa.is_confirmed = TRUE AND aa.send_status IN ('pending', 'failed', 'confirmed'))

ORDER BY act.id, aa.is_active DESC, aa.assigned_at DESC

-- Actividades de prueba (horas UTC)
INSERT INTO activities (id, satellite_id, orbit_number, start_time, end_time, duration, status, priority, created_at, updated_at) VALUES
--ID        Satelitte Orbita   Inicio                       Fin                         Duracion  Estado        Prioridad  Creado                         Actualizado
-- Actividades para ADD (nuevas, nunca enviadas)
( 'ACT011', '27424',  '12345', NOW() + INTERVAL '2 hours',  NOW() + INTERVAL '3 hours', 3600,     'authorized', 'high',    NOW() - INTERVAL '1 hour',     NULL),
( 'ACT012', '27424',  '12346', NOW() + INTERVAL '4 hours',  NOW() + INTERVAL '5 hours', 3600,     'authorized', 'medium',  NOW() - INTERVAL '45 minutes', NULL),
-- Actividades para UPDATE (modificadas después del último envío)
( 'ACT013', '27424',  '12347', NOW() + INTERVAL '6 hours',  NOW() + INTERVAL '7 hours', 3600,     'authorized', 'high',    NOW() - INTERVAL '2 hours',    NOW()),
( 'ACT014', '39084',  '12348', NOW() + INTERVAL '8 hours',  NOW() + INTERVAL '9 hours', 3600,     'authorized', 'medium',  NOW() - INTERVAL '3 hours',    NOW() - INTERVAL '30 minutes'),
-- Actividades para DELETE (canceladas)
( 'ACT015', '39084',  '12349', NOW() + INTERVAL '10 hours', NOW() + INTERVAL '11 hours', 3600,    'canceled',   'low',     NOW() - INTERVAL '4 hours',    NOW()),
( 'ACT016', '27424',  '12350', NOW() + INTERVAL '12 hours', NOW() + INTERVAL '13 hours', 3600,    'canceled',   'medium',  NOW() - INTERVAL '5 hours',    NOW() - INTERVAL '15 minutes'),
-- Actividades para REASSIGN (reasignadas a otra antena)
( 'ACT017', '27424',  '12357', NOW() + INTERVAL '14 hours', NOW() + INTERVAL '15 hours', 3600,    'authorized', 'high',    NOW() - INTERVAL '6 hours',    NOW() - INTERVAL '10 minutes'),
( 'ACT018', '39084',  '12358', NOW() + INTERVAL '16 hours', NOW() + INTERVAL '17 hours', 3600,    'authorized', 'critical',NOW() - INTERVAL '7 hours',    NOW() - INTERVAL '5 minutes'),
-- Actividad con fallo de envío anterior
( 'ACT019', '27424',  '12359', NOW() + INTERVAL '18 hours', NOW() + INTERVAL '19 hours', 3600,    'authorized', 'high',    NOW() - INTERVAL '8 hours',    NOW() - INTERVAL '20 minutes'),
-- Actividad con múltiples actualizaciones
( 'ACT020', '39084',  '12360', NOW() + INTERVAL '20 hours', NOW() + INTERVAL '21 hours', 3600,    'authorized', 'medium',  NOW() - INTERVAL '9 hours',    NOW());


-- Asignaciones para actividades de ADD (nuevas)
INSERT INTO activity_assignments (id, activity_id, antenna_id, is_active, assigned_at, is_confirmed, confirmed_at, send_status) VALUES

-- ID      Actividad  Antena    Activa  Asignada                        Confirmada  HorarioConfirmacion             Estado
-- Asignaciones para actividades de ADD (nuevas, nunca enviadas)
('ASG001',  'ACT011', 'ANT001', TRUE,   NOW() - INTERVAL '50 minutes',  TRUE,       NOW() - INTERVAL '45 minutes',  'pending'),
('ASG002',  'ACT012', 'ANT002', TRUE,   NOW() - INTERVAL '40 minutes',  TRUE,       NOW() - INTERVAL '35 minutes',  'pending'),
-- Asignaciones para actividades de UPDATE (ya enviadas pero modificadas)
('ASG003',  'ACT013', 'ANT001', FALSE,  NOW() - INTERVAL '2 hours',     TRUE,       NOW() - INTERVAL '1 hour',      'confirmed'),
('ASG004',  'ACT013', 'ANT001', FALSE,  NOW() - INTERVAL '3 hours',     TRUE,       NOW() - INTERVAL '2 hours',     'confirmed'),
('ASG011',  'ACT013', 'ANT001', TRUE,   NOW() - INTERVAL '3 minutes',   TRUE,       NOW() - INTERVAL '2 hours',     'pending'),
-- Asignaciones para actividades de DELETE (canceladas)
('ASG005',  'ACT015', 'ANT002', FALSE,  NOW() - INTERVAL '5 hours',     TRUE,       NOW() - INTERVAL '3 hours',     'confirmed'),
('ASG006',  'ACT015', 'ANT002', FALSE,  NOW() - INTERVAL '4 minutes',   TRUE,       NOW() - INTERVAL '4 hours',     'pending'),   ---> NO HACE NADA
('ASG012',  'ACT016', 'ANT004', FALSE,  NOW() - INTERVAL '5 hours',     TRUE,       NOW() - INTERVAL '3 hours',     'confirmed'),
('ASG013',  'ACT016', 'ANT004', TRUE,   NOW() - INTERVAL '4 minutes',   TRUE,       NOW() - INTERVAL '4 hours',     'confirmed'), ---> ya fue enviado a ANT004
-- Asignaciones para actividades de REASSIGN (historial de asignaciones)
('ASG007a', 'ACT017', 'ANT001', FALSE,  NOW() - INTERVAL '6 hours',     TRUE,       NOW() - INTERVAL '5 hours',     'confirmed'), ---> Antigua asignación (inactiva)
('ASG007b', 'ACT017', 'ANT003', TRUE,   NOW() - INTERVAL '10 minutes',  TRUE,       NOW() - INTERVAL '5 minutes',   'pending'),   ---> Nueva asignación (activa)
('ASG008a', 'ACT018', 'ANT002', FALSE,  NOW() - INTERVAL '7 hours',     TRUE,       NOW() - INTERVAL '6 hours',     'confirmed'),
('ASG008b', 'ACT018', 'ANT004', TRUE,   NOW() - INTERVAL '15 minutes',  TRUE,       NOW() - INTERVAL '5 minutes',   'confirmed'), ---> Asignacion ya mandada a ANT004
-- Asignación con fallo de envío
('ASG009',  'ACT019', 'ANT001', TRUE,   NOW() - INTERVAL '8 hours',     TRUE,       NOW() - INTERVAL '7 hours',     'failed'),
-- Asignación para actividad con múltiples actualizaciones
('ASG010a', 'ACT020', 'ANT003', FALSE,  NOW() - INTERVAL '9 hours',     TRUE,       NOW() - INTERVAL '8 hours',     'confirmed'),
('ASG010b', 'ACT020', 'ANT003', TRUE,   NOW() - INTERVAL '20 minutes',  TRUE,       NOW() - INTERVAL '10 minutes',  'confirmed');

-- Agregamos las configuraciones de las actividades para las antenas
INSERT INTO activity_configuration (id, satellite_id, antenna_id, config_number, description, is_active) VALUES
('AC011', '27424', 'ANT001', 1, 'Configuración estándar para AQUA', TRUE),
('AC021', '27424', 'ANT002', 2, 'Configuración estándar para AQUA', TRUE),
('AC031', '27424', 'ANT003', 3, 'Configuración estándar para AQUA', TRUE),
('AC041', '27424', 'ANT004', 4, 'Configuración estándar para AQUA', TRUE),
('AC051', '39084', 'ANT001', 1, 'Configuración estándar para Landsat8', TRUE),
('AC061', '39084', 'ANT002', 2, 'Configuración estándar para Landsat8', TRUE),
('AC071', '39084', 'ANT003', 3, 'Configuración estándar para Landsat8', TRUE),
('AC081', '39084', 'ANT004', 4, 'Configuración estándar para Landsat8', TRUE);

delete from activity_assignments