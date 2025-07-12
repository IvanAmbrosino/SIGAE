-- Tabla de usuarios
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
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

-- Tabla de antenas
CREATE TABLE antennas (
    id VARCHAR(36) PRIMARY KEY,
    ground_station_id VARCHAR(36) REFERENCES ground_stations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    model VARCHAR(255),
    min_elevation DECIMAL(5, 2),
    operational_status VARCHAR(20) CHECK (operational_status IN ('operational', 'maintenance', 'out_of_service')),
    quality_level VARCHAR(10) CHECK (quality_level IN ('high', 'medium', 'low')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de capacidades de antena
CREATE TABLE antenna_capabilities (
    id VARCHAR(36) PRIMARY KEY,
    antenna_id VARCHAR(36) REFERENCES antennas(id) ON DELETE CASCADE,
    frequency_band VARCHAR(10) CHECK (frequency_band IN ('S', 'X', 'Ku', 'Ka', 'other')),
    min_frequency DECIMAL(10, 2),
    max_frequency DECIMAL(10, 2),
    polarization VARCHAR(10) CHECK (polarization IN ('linear', 'circular', 'dual')),
    data_rate DECIMAL(10, 2)
);

-- Tabla de satélites
CREATE TABLE satellites (
    id VARCHAR(20) PRIMARY KEY,  -- NORAD ID suele ser un número no muy largo, ajustar tamaño si querés
    name VARCHAR(255) NOT NULL,
    priority_level VARCHAR(10) CHECK (priority_level IN ('critical', 'high', 'medium', 'low')),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de requisitos de satélite
CREATE TABLE satellite_requirements (
    id VARCHAR(36) PRIMARY KEY,
    satellite_id VARCHAR(36) REFERENCES satellites(id) ON DELETE CASCADE,
    frequency_band VARCHAR(10) CHECK (frequency_band IN ('S', 'X', 'Ku', 'Ka', 'other')),
    min_frequency DECIMAL(10, 2),
    max_frequency DECIMAL(10, 2),
    polarization VARCHAR(10) CHECK (polarization IN ('linear', 'circular', 'dual')),
    min_elevation DECIMAL(5, 2),
    min_duration INTEGER
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
    epoch TIMESTAMP NOT NULL,
    source VARCHAR(20) CHECK (source IN ('spacetrack', 'manual', 'api')),
    is_valid BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de actividades
CREATE TABLE activities (
    id VARCHAR(36) PRIMARY KEY,
    satellite_id VARCHAR(36) REFERENCES satellites(id) ON DELETE CASCADE,
    orbit_number VARCHAR(255),
    start_time TIMESTAMP NOT NULL,
    max_elevation_time TIMESTAMP,
    end_time TIMESTAMP NOT NULL,
    duration INTEGER NOT NULL,
    status VARCHAR(20) CHECK (status IN ('new', 'assigned', 'unassigned', 'pending', 'authorized', 'planned', 'modified', 'updated', 'critical')),
    priority VARCHAR(10) CHECK (priority IN ('critical', 'high', 'medium', 'low')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (satellite_id, orbit_number)
);

-- Tabla de asignaciones de actividad
CREATE TABLE activity_assignments (
    id VARCHAR(36) PRIMARY KEY,
    activity_id VARCHAR(36) REFERENCES activities(id) ON DELETE CASCADE,
    antenna_id VARCHAR(36) REFERENCES antennas(id) ON DELETE CASCADE,
    assigned_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_confirmed BOOLEAN DEFAULT FALSE,
    confirmed_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    confirmed_at TIMESTAMP
);

-- Tabla de requisitos de actividad
CREATE TABLE activity_requirements (
    id VARCHAR(36) PRIMARY KEY,
    activity_id VARCHAR(36) REFERENCES activities(id) ON DELETE CASCADE,
    frequency_band VARCHAR(10) CHECK (frequency_band IN ('S', 'X', 'Ku', 'Ka', 'other')),
    min_frequency DECIMAL(10, 2),
    max_frequency DECIMAL(10, 2),
    polarization VARCHAR(10) CHECK (polarization IN ('linear', 'circular', 'dual'))
);

-- Tabla de reservaciones
CREATE TABLE reservations (
    id VARCHAR(36) PRIMARY KEY,
    antenna_id VARCHAR(36) REFERENCES antennas(id) ON DELETE CASCADE,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    purpose VARCHAR(20) CHECK (purpose IN ('maintenance', 'client', 'other')),
    description TEXT,
    requested_by VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE,
    approved_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(20) CHECK (status IN ('pending', 'approved', 'rejected', 'completed')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de configuraciones del sistema
CREATE TABLE system_configurations (
    id VARCHAR(36) PRIMARY KEY,
    config_key VARCHAR(255) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    data_type VARCHAR(10) CHECK (data_type IN ('string', 'number', 'boolean', 'json')),
    description TEXT,
    updated_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
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
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de historial de actividades
CREATE TABLE activity_history (
    id VARCHAR(36) PRIMARY KEY,
    activity_id VARCHAR(36) REFERENCES activities(id) ON DELETE CASCADE,
    changed_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    change_type VARCHAR(20) CHECK (change_type IN ('create', 'update', 'status_change', 'assignment')),
    old_values JSONB,
    new_values JSONB,
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
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