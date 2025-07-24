SELECT satellite_id, antenna_id, config_number
FROM activity_configuration
WHERE is_active = TRUE
AND satellite_id IN (
    SELECT a.satellite_id UNIQUE
    FROM activities a
    JOIN activity_assignments aa ON a.id = aa.activity_id
    WHERE aa.is_confirmed = TRUE 
        AND a.status IN ('planned', 'authorized', 'assigned')
        AND a.start_time > NOW() - INTERVAL '4 year'
        AND a.end_time < NOW() + INTERVAL '72 hour'
    )


SELECT act.*, aa.*,
    ant.name AS antenna_name,
    ant.code AS antenna_code,
    sat.name AS satellite_name,
    ac.config_number AS config_number
FROM activities act
JOIN activity_assignments aa ON act.id = aa.activity_id
JOIN antennas ant ON aa.antenna_id = ant.id
JOIN satellites sat ON act.satellite_id = sat.id
LEFT JOIN activity_configuration ac ON (
    ac.satellite_id = act.satellite_id 
    AND ac.antenna_id = aa.antenna_id
    AND ac.is_active = TRUE
)
WHERE aa.is_confirmed = TRUE 
    AND act.status IN ('planned', 'authorized', 'assigned')
    AND act.start_time > NOW() - INTERVAL '4 year'
    AND act.end_time < NOW() + INTERVAL '72 hour'


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
    -- Determinacion de la Accion Requerida
    CASE -- Primero determina para cada actividad qué acción es requerida
        -- Actividades canceladas (status cambiado a unassigned)
        WHEN act.status IN ('canceled') THEN 'delete'
        -- Actividades modificadas (ya fueron enviadas pero tienen actualizaciones)
        -- Se verifica si la última vez que se envió es anterior a la última actualización
        WHEN aa.last_sent_at IS NOT NULL AND act.updated_at > aa.last_sent_at THEN 'update'
        -- Nuevas actividades que nunca se enviaron
        ELSE 'add'
    END AS required_action,
    -- Campos para control de envíos (fechas)
    act.updated_at,
    aa.last_sent_at,
    aa.send_status
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
    act.end_time < NOW() + INTERVAL '72 hour' AND
    act.start_time > NOW() - INTERVAL '3 year' AND
    (
        -- Caso 1: Asignaciones confirmadas que necesitan ser enviadas/actualizadas
        -- Para ser ADD, debe cumplir:
            -- 1. La asignación debe estar confirmada (is_confirmed = TRUE)
            -- 2. La actividad debe estar en estado autorizado (authorized)
            -- 3. Si nunca se envió, no se registró fecha (last_sent) o en estado 'pending'
        -- Para ser UPDATE, debe cumplor:
            -- 1. La asignación debe estar confirmada (is_confirmed = TRUE)
            -- 2. La actividad debe estar en estado autorizado (authorized) o planificado (planned)
            -- 3. Si hay actualizaciones desde la ultima vez que se envió (act.updated_at > aa.last_sent_at)
            -- 4. O si el ultimo envio resultó en error (send_status = 'failed')
        (
            aa.is_confirmed = TRUE                      -- Se envían si esta confirmada
            AND act.status IN ('authorized', 'planned') -- Se envían si esta en estado autorizado (add) o planificado (update)
            AND (
                aa.last_sent_at IS NULL                 -- Si nunca se envió, no se registró fecha (add)
                OR act.updated_at > aa.last_sent_at     -- Si hay actualizaciones desde la ultima vez que se envió (update)
                OR aa.send_status = 'failed')           -- Si el ultimo envio resultó en error (update)
        )
        -- Caso 2: Asignaciones que deben ser eliminadas (actividad cancelada)
        -- En este caso, para cancelar la actividad se debe verificar que:
            -- 1. La actividad esté en estado cancelado (canceled)
            -- 2. La asignación esté confirmada (is_confirmed = TRUE)
            -- 3. Que la fecha de actualización de la actividad sea posterior a la última vez que se envió (act.updated_at > aa.last_sent_at)
        OR (
            act.status IN ('canceled') -- Estan en estado canceled
            AND aa.is_confirmed = TRUE -- Estan confirmadas (fueron cargadas anteriormente)
            AND aa.last_sent_at IS NOT NULL AND act.updated_at > aa.last_sent_at -- Si hay actualizaciones desde la ultima vez que se envió
            AND aa.send_status = 'confirmed'  -- Si hay indicios de carga (significa que se cargaron en algun momento)
        )
    )
ORDER BY 
    act.priority DESC,
    act.start_time ASC;
