-- Tabla de usuarios
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP	
);

-- Tabla de roles
CREATE TABLE roles (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT
);

-- Tabla de relación usuario-rol
CREATE TABLE user_roles (
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE,
    role_id VARCHAR(36) REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- Tabla de permisos
CREATE TABLE permissions (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT
);

-- Tabla de relación rol-permiso
CREATE TABLE role_permissions (
    role_id VARCHAR(36) REFERENCES roles(id) ON DELETE CASCADE,
    permission_id VARCHAR(36) REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- Tabla de estaciones terrestres
CREATE TABLE ground_stations (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    altitude DECIMAL(10, 2),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

-- Tabla de configuraciones de estaciones terrestres
CREATE TABLE ground_station_configurations (
    id VARCHAR(36) PRIMARY KEY,
    ground_station_id VARCHAR(36) REFERENCES ground_stations(id) ON DELETE CASCADE,
    default_propagation_hours INTEGER DEFAULT 24,
    night_start_hour INTEGER CHECK (night_start_hour >= 0 AND night_start_hour < 24),
    night_end_hour INTEGER CHECK (night_end_hour >= 0 AND night_end_hour < 24),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de antenas
CREATE TABLE antennas (
    id VARCHAR(36) PRIMARY KEY,
    ground_station_id VARCHAR(36) REFERENCES ground_stations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    model VARCHAR(255),
    min_elevation DECIMAL(5, 2),
    operational_status VARCHAR(20) CHECK (operational_status IN ('operational', 'maintenance', 'out_of_service')),
    quality_level VARCHAR(10) CHECK (quality_level IN ('high', 'medium', 'low')),
    is_active BOOLEAN DEFAULT TRUE,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    altitude DECIMAL(10, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de capacidades de antena
--CREATE TABLE antenna_capabilities (
--    id VARCHAR(36) PRIMARY KEY,
--    antenna_id VARCHAR(36) REFERENCES antennas(id) ON DELETE CASCADE,
--    frequency_band VARCHAR(10) CHECK (frequency_band IN ('S', 'X', 'Ku', 'Ka', 'other')),
--    min_frequency DECIMAL(10, 2),
--    max_frequency DECIMAL(10, 2),
--    polarization VARCHAR(10) CHECK (polarization IN ('linear', 'circular', 'dual')),
--    data_rate DECIMAL(10, 2)
--);

-- Tabla de satélites
CREATE TABLE satellites (
    id VARCHAR(20) PRIMARY KEY,  -- NORAD ID suele ser un número no muy largo
    name VARCHAR(255) NOT NULL,
    priority_level VARCHAR(10) CHECK (priority_level IN ('critical', 'high', 'medium', 'low')),
    description TEXT,

    -- Eliminación lógica
    is_active BOOLEAN DEFAULT TRUE,  -- Usado como soft delete

    -- Propagación y visibilidad
    can_propagate BOOLEAN DEFAULT TRUE,
    allow_daytime_propagation BOOLEAN DEFAULT TRUE,
    allow_nighttime_propagation BOOLEAN DEFAULT TRUE,
    min_elevation DECIMAL(5, 2),
    max_elevation DECIMAL(5, 2),
    
    -- Nuevo campo: indica si se puede obtener info desde una API externa
    can_fetch_from_api BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de compatibilidad satélite-antena
CREATE TABLE satellite_antenna_compatibility (
    satellite_id VARCHAR(36) REFERENCES satellites(id) ON DELETE CASCADE,
    antenna_id VARCHAR(36) REFERENCES antennas(id) ON DELETE CASCADE,
    PRIMARY KEY (satellite_id, antenna_id)
);

-- Tabla de datos TLE
CREATE TABLE tle_data (
    id VARCHAR(36) PRIMARY KEY,
    satellite_id VARCHAR(36) REFERENCES satellites(id) ON DELETE CASCADE,
    line1 VARCHAR(255) NOT NULL,
    line2 VARCHAR(255) NOT NULL,
    epoch TIMESTAMPTZ NOT NULL,
    source VARCHAR(20) CHECK (source IN ('spacetrack', 'manual', 'api')),
    is_valid BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de actividades
CREATE TABLE activities (
    id VARCHAR(36) PRIMARY KEY,
    satellite_id VARCHAR(36) REFERENCES satellites(id) ON DELETE CASCADE,
    orbit_number VARCHAR(255),
    start_time TIMESTAMPTZ NOT NULL,
    max_elevation_time TIMESTAMP,
    max_elevation DECIMAL(5, 2),
    end_time TIMESTAMPTZ NOT NULL,
    duration INTEGER NOT NULL,
    status VARCHAR(20) CHECK (status IN ('new', 'assigned', 'unassigned', 'pending', 'authorized', 'planned', 'modified', 'updated', 'critical')),
    priority VARCHAR(10) CHECK (priority IN ('critical', 'high', 'medium', 'low')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (satellite_id, orbit_number)
);

-- Tabla de configuracion de actividad
CREATE TABLE activity_configuration (
    id VARCHAR(36) PRIMARY KEY,
    satellite_id VARCHAR(36) REFERENCES satellites(id) ON DELETE CASCADE,
    antenna_id VARCHAR(36) REFERENCES antennas(id) ON DELETE CASCADE,

    -- En caso que haya mas de una configuracion por par satellite-antena
    config_number INTEGER NOT NULL DEFAULT 1,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE

);

-- Tabla de asignaciones de actividad
CREATE TABLE activity_assignments (
    id VARCHAR(36) PRIMARY KEY,
    activity_id VARCHAR(36) REFERENCES activities(id) ON DELETE CASCADE,
    antenna_id VARCHAR(36) REFERENCES antennas(id) ON DELETE CASCADE,
    --assigned_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_confirmed BOOLEAN DEFAULT FALSE,
    --confirmed_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    confirmed_at TIMESTAMP
);

-- Tabla de requisitos de actividad
--CREATE TABLE activity_requirements (
--    id VARCHAR(36) PRIMARY KEY,
--    activity_id VARCHAR(36) REFERENCES activities(id) ON DELETE CASCADE,
--    frequency_band VARCHAR(10) CHECK (frequency_band IN ('S', 'X', 'Ku', 'Ka', 'other')),
--    min_frequency DECIMAL(10, 2),
--    max_frequency DECIMAL(10, 2),
--    polarization VARCHAR(10) CHECK (polarization IN ('linear', 'circular', 'dual'))
--);

-- Tabla de reservaciones
CREATE TABLE reservations (
    id VARCHAR(36) PRIMARY KEY,
    antenna_id VARCHAR(36) REFERENCES antennas(id) ON DELETE CASCADE,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    purpose VARCHAR(20) CHECK (purpose IN ('maintenance', 'client', 'other')),
    description TEXT,
    requested_by VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE,
    approved_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(20) CHECK (status IN ('pending', 'approved', 'rejected', 'completed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de configuraciones del sistema
CREATE TABLE system_configurations (
    id VARCHAR(36) PRIMARY KEY,
    config_key VARCHAR(255) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    data_type VARCHAR(10) CHECK (data_type IN ('string', 'number', 'boolean', 'json')),
    description TEXT,
    updated_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de notificaciones
CREATE TABLE notifications (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    notification_type VARCHAR(20) CHECK (notification_type IN ('activity', 'reservation', 'system', 'alert')),
    related_entity_type VARCHAR(20) CHECK (related_entity_type IN ('activity', 'reservation', 'antenna', 'satellite', 'none')),
    related_entity_id VARCHAR(36),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de historial de actividades
CREATE TABLE activity_history (
    id VARCHAR(36) PRIMARY KEY,
    activity_id VARCHAR(36) REFERENCES activities(id) ON DELETE CASCADE,
    changed_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    change_type VARCHAR(20) CHECK (change_type IN ('create', 'update', 'status_change', 'assignment')),
    old_values JSONB,
    new_values JSONB,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Crear función para actualizar automáticamente los campos updated_at
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Crear triggers para las tablas que necesitan actualización automática de timestamp
CREATE TRIGGER update_users_timestamp
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_antennas_timestamp
BEFORE UPDATE ON antennas
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_satellites_timestamp
BEFORE UPDATE ON satellites
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_activities_timestamp
BEFORE UPDATE ON activities
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_reservations_timestamp
BEFORE UPDATE ON reservations
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_system_configurations_timestamp
BEFORE UPDATE ON system_configurations
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- Insertar satélites de prueba
INSERT INTO satellites
(id, name, priority_level, description, is_active, can_propagate, allow_daytime_propagation, allow_nighttime_propagation, min_elevation, max_elevation, can_fetch_from_api, created_at, updated_at)
VALUES
('25544', 'ISS', 'high', 'Estación Espacial Internacional', TRUE, TRUE, TRUE, TRUE, 10.0, 90.0, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('27424', 'AQUA', 'medium', 'Satélite de observación de la NASA', TRUE, TRUE, FALSE, TRUE, 15.0, 85.0, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('39084', 'LANDSAT-8', 'critical', 'Satélite de observación terrestre', TRUE, TRUE, TRUE, FALSE, 20.0, 88.0, FALSE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('25338', 'NOAA 15', 'low', 'Satélite meteorológico NOAA 15', TRUE, TRUE, TRUE, TRUE, 10.0, 85.0, FALSE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('33591', 'NOAA 19', 'medium', 'NOAA weather satellite', TRUE, TRUE, TRUE, TRUE, 5.00, 90.00, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('28654', 'TDRS 11', 'critical', 'Tracking and Data Relay Satellite', TRUE, TRUE, TRUE, TRUE, 5.00, 90.00, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('39430', 'STARLINK-1007', 'low', 'Starlink satellite', TRUE, TRUE, TRUE, TRUE, 25.00, 90.00, FALSE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- Insertar estación terrestre por defecto: Córdoba, Córdoba
INSERT INTO ground_stations
(id, name, location, latitude, longitude, altitude, description, is_active)
VALUES
('ETC', 'Estación Terrena Córdoba', 'Córdoba, Córdoba, Argentina', -31.4201, -64.1888, 360.0, 'Estación principal ubicada en Córdoba, Argentina.', TRUE);

-- Insertar configuración por defecto para la estación Córdoba
INSERT INTO ground_station_configurations
(id, ground_station_id, default_propagation_hours, night_start_hour, night_end_hour, created_at, updated_at)
VALUES
('ETC-CONF-001', 'ETC', 72, 20, 6, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP); 

-- Insercion de Antenas de Estacion Terrena Cordoba
INSERT INTO antennas (id, ground_station_id, name, code, model, min_elevation, operational_status, quality_level, is_active, latitude, longitude, altitude) VALUES
('ANT001', 'ETC', 'ANTENA 13', 'ANTDTRM01', 'Datron 13m', 5.00, 'operational', 'high', TRUE, -31.524986, -64.462739, 733.04),
('ANT002', 'ETC', 'ANTENA 7.3', 'ANTDTRG01', 'Datron 7m', 10.00, 'operational', 'medium', TRUE, -31.524933, -64.46315, 730.84),
('ANT003', 'ETC', 'ANTENA 13.5', 'ANTVSTM01', 'Viasat 11m', 5.00, 'operational', 'high', TRUE, -31.525334, -64.461689, 726.95),
('ANT004', 'ETC', 'ANTENA 5.4', 'ANTVSTE01', 'Viasat 13m', 5.00, 'maintenance', 'high', FALSE, -31.523200, -64.460335, 723.00),
('ANT005', 'ETC', 'ANTENA 6.1', 'ANTVSTFM01', 'Viasat 11m', 5.00, 'operational', 'high', TRUE, -31.522133, -64.459803, 720.49);


INSERT INTO satellite_antenna_compatibility (satellite_id, antenna_id) VALUES
('25544', 'ANT001'),
('25544', 'ANT002'),
('25544', 'ANT003'),
('25544', 'ANT005'),
('33591', 'ANT001'),
('33591', 'ANT003'),
('33591', 'ANT005'),
('25338', 'ANT001'),
('25338', 'ANT005'),
('28654', 'ANT001'),
('28654', 'ANT003'),
('28654', 'ANT005'),
('39430', 'ANT001'),
('27424', 'ANT001'),
('39430', 'ANT003');

-- Insertar configuraciones de actividad para satélites/antenna
INSERT INTO activity_configuration (id, satellite_id, antenna_id, config_number, description, is_active) VALUES
('AC001', '25544', 'ANT001', 1, 'Configuración estándar para ISS', TRUE),
('AC002', '25544', 'ANT001', 2, 'Configuración de alta ganancia para ISS', TRUE),
('AC003', '33591', 'ANT001', 1, 'Configuración para NOAA', TRUE),
('AC004', '25338', 'ANT001', 1, 'Configuración para HST', TRUE),
('AC005', '28654', 'ANT003', 1, 'Configuración para TDRS', TRUE),
('AC006', '33591', 'ANT003', 2, 'Configuración para NOAA', TRUE);

-- Insertar Actividades de prueba en diferentes estados
INSERT INTO activities (id, satellite_id, orbit_number, start_time, max_elevation_time, max_elevation, end_time, duration, status, priority) VALUES
('ACT001', '25544', '12345', '2023-06-01 08:00:00+00', '2023-06-01 08:15:00', 78.50, '2023-06-01 08:30:00+00', 1800, 'planned', 'high'),
('ACT002', '33591', '67890', '2023-06-01 09:30:00+00', '2023-06-01 09:45:00', 65.20, '2023-06-01 10:00:00+00', 1800, 'authorized', 'medium'),
('ACT003', '25338', '54321', '2023-06-01 11:00:00+00', '2023-06-01 11:20:00', 82.10, '2023-06-01 11:40:00+00', 2400, 'assigned', 'high'),
('ACT004', '28654', '98765', '2023-06-01 12:30:00+00', '2023-06-01 12:40:00', 45.70, '2023-06-01 12:50:00+00', 1200, 'pending', 'critical'),
('ACT005', '39430', '13579', '2023-06-01 14:00:00+00', '2023-06-01 14:05:00', 32.80, '2023-06-01 14:10:00+00', 600, 'new', 'low');

-- Insertar asignaciones de actividad sin usuarios
INSERT INTO activity_assignments (id, activity_id, antenna_id, is_confirmed, confirmed_at) VALUES
('ASG001', 'ACT001', 'ANT001', TRUE, NULL),
('ASG002', 'ACT002', 'ANT003', TRUE, NULL),
('ASG003', 'ACT003', 'ANT001', TRUE, NULL),
('ASG004', 'ACT004', 'ANT003', TRUE, NULL),
('ASG005', 'ACT005', 'ANT001', TRUE, NULL)


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