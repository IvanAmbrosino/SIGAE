-- Tablas principales
CREATE TABLE estaciones_terrenas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    latitud DOUBLE PRECISION NOT NULL,
    longitud DOUBLE PRECISION NOT NULL,
    descripcion TEXT,
    activa BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE niveles_calidad (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    descripcion TEXT,
    nivel INTEGER UNIQUE NOT NULL
);

CREATE TABLE bandas_frecuencia (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    frecuencia_min DOUBLE PRECISION NOT NULL,
    frecuencia_max DOUBLE PRECISION NOT NULL,
    descripcion TEXT
);

CREATE TABLE modulaciones (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT
);

CREATE TABLE antenas (
    id SERIAL PRIMARY KEY,
    identificador VARCHAR(50) NOT NULL UNIQUE,
    estacion_id INTEGER REFERENCES estaciones_terrenas(id) ON DELETE CASCADE,
    nivel_calidad_id INTEGER REFERENCES niveles_calidad(id),
    estado VARCHAR(20) CHECK (estado IN ('OPERATIVA', 'MANTENIMIENTO', 'RESERVADA', 'FALLADA')) DEFAULT 'OPERATIVA',
    descripcion TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE satelites (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    norad_id VARCHAR(50) UNIQUE,
    prioridad INTEGER NOT NULL DEFAULT 3,
    fuente_tle VARCHAR(100),
    descripcion TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tles (
    id SERIAL PRIMARY KEY,
    linea1 VARCHAR(200) NOT NULL,
    linea2 VARCHAR(200) NOT NULL,
    satelite_id INTEGER REFERENCES satelites(id) ON DELETE CASCADE,
    fecha_obtencion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    valido_hasta TIMESTAMP WITH TIME ZONE
);

CREATE TABLE actividades (
    id SERIAL PRIMARY KEY,
    satelite_id INTEGER REFERENCES satelites(id) ON DELETE CASCADE,
    antena_id INTEGER REFERENCES antenas(id) ON DELETE SET NULL,
    orbita_numero INTEGER,
    inicio TIMESTAMP WITH TIME ZONE NOT NULL,
    max_elevacion TIMESTAMP WITH TIME ZONE,
    fin TIMESTAMP WITH TIME ZONE NOT NULL,
    duracion INTEGER, -- en segundos
    estado VARCHAR(20) CHECK (estado IN (
        'NEW', 'ASSIGNED', 'UNASSIGNED', 'PENDING', 
        'AUTHORIZED', 'PLANNED', 'LOADED', 'MODIFIED', 
        'UPDATED', 'CRITICAL'
    )) DEFAULT 'NEW',
    prioridad INTEGER NOT NULL DEFAULT 3,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE recursos_adicionales (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(50) NOT NULL,
    descripcion TEXT,
    requerido BOOLEAN DEFAULT FALSE,
    asignado BOOLEAN DEFAULT FALSE,
    actividad_id INTEGER REFERENCES actividades(id) ON DELETE CASCADE
);

CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) CHECK (rol IN ('ADMINISTRADOR', 'PLANIFICADOR', 'OPERADOR', 'LECTURA')) DEFAULT 'LECTURA',
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE notificaciones (
    id SERIAL PRIMARY KEY,
    mensaje TEXT NOT NULL,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
    leida BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE configuraciones_sistema (
    id SERIAL PRIMARY KEY,
    clave VARCHAR(50) NOT NULL UNIQUE,
    valor TEXT,
    descripcion TEXT,
    editable BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tablas de relación muchos-a-muchos
CREATE TABLE antenas_bandas (
    antena_id INTEGER REFERENCES antenas(id) ON DELETE CASCADE,
    banda_id INTEGER REFERENCES bandas_frecuencia(id) ON DELETE CASCADE,
    PRIMARY KEY (antena_id, banda_id)
);

CREATE TABLE antenas_modulaciones (
    antena_id INTEGER REFERENCES antenas(id) ON DELETE CASCADE,
    modulacion_id INTEGER REFERENCES modulaciones(id) ON DELETE CASCADE,
    PRIMARY KEY (antena_id, modulacion_id)
);

CREATE TABLE satelites_bandas (
    satelite_id INTEGER REFERENCES satelites(id) ON DELETE CASCADE,
    banda_id INTEGER REFERENCES bandas_frecuencia(id) ON DELETE CASCADE,
    PRIMARY KEY (satelite_id, banda_id)
);

CREATE TABLE satelites_modulaciones (
    satelite_id INTEGER REFERENCES satelites(id) ON DELETE CASCADE,
    modulacion_id INTEGER REFERENCES modulaciones(id) ON DELETE CASCADE,
    PRIMARY KEY (satelite_id, modulacion_id)
);

-- Índices para mejorar el rendimiento
CREATE INDEX idx_actividades_estado ON actividades(estado);
CREATE INDEX idx_actividades_satelite ON actividades(satelite_id);
CREATE INDEX idx_actividades_antena ON actividades(antena_id);
CREATE INDEX idx_actividades_tiempo ON actividades(inicio, fin);
CREATE INDEX idx_tles_satelite ON tles(satelite_id);
CREATE INDEX idx_tles_fecha ON tles(fecha_obtencion);

-- Datos iniciales
INSERT INTO niveles_calidad (nombre, descripcion, nivel) VALUES 
('ALTA', 'Antena con máxima confiabilidad y capacidades completas', 1),
('MEDIA', 'Antena con capacidades estándar', 2),
('BAJA', 'Antena con capacidades limitadas o en degradación', 3);

INSERT INTO bandas_frecuencia (nombre, frecuencia_min, frecuencia_max, descripcion) VALUES
('S', 2000, 4000, 'Banda S para comunicaciones satelitales'),
('X', 8000, 12000, 'Banda X para alta velocidad de datos'),
('Ku', 12000, 18000, 'Banda Ku para comunicaciones avanzadas'),
('Ka', 26000, 40000, 'Banda Ka para alta capacidad');

INSERT INTO modulaciones (tipo, descripcion) VALUES
('QPSK', 'Modulación por desplazamiento de cuadratura'),
('8PSK', 'Modulación por desplazamiento de fase de 8 niveles'),
('16APSK', 'Modulación de amplitud y fase de 16 niveles'),
('32APSK', 'Modulación de amplitud y fase de 32 niveles');

INSERT INTO configuraciones_sistema (clave, valor, descripcion) VALUES
('elevacion_minima', '10', 'Elevación mínima en grados para considerar una pasada válida'),
('tiempo_minimo_pasada', '300', 'Duración mínima en segundos para considerar una pasada válida'),
('dias_planificacion', '7', 'Número de días hacia adelante para planificar'),
('tle_update_interval', '86400', 'Intervalo en segundos para actualizar TLEs (24 horas)');

-- Función para actualizar timestamps
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = CURRENT_TIMESTAMP;
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para actualización automática de timestamps
CREATE TRIGGER update_estaciones_timestamp
BEFORE UPDATE ON estaciones_terrenas
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_antenas_timestamp
BEFORE UPDATE ON antenas
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_satelites_timestamp
BEFORE UPDATE ON satelites
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_actividades_timestamp
BEFORE UPDATE ON actividades
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_usuarios_timestamp
BEFORE UPDATE ON usuarios
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_configuraciones_timestamp
BEFORE UPDATE ON configuraciones_sistema
FOR EACH ROW EXECUTE FUNCTION update_timestamp();