import psycopg2
from psycopg2.extras import execute_values
from contextlib import contextmanager
from datetime import datetime
import uuid 
from typing import List

from domain.tle_pass import TleData, PassActivity


@contextmanager
def get_db_connection(config):
    conn = psycopg2.connect(
        dbname=config['dbname'],
        user=config['user'],
        password=config['password'],
        host=config['host'],
        port=config.get('port', 5432)
    )
    try:
        yield conn
    finally:
        conn.close()

def save_pass_activities(conn, pasadas: List[PassActivity]):

     # Filtrar duplicados por (satellite_id, orbit_number)
    seen = set()
    unique_pasadas = []
    for pasada in pasadas:
        key = (pasada.satellite_id, pasada.orbit_number)
        if key not in seen:
            seen.add(key)
            unique_pasadas.append(pasada)
    sql = """
    INSERT INTO activities
    (id, satellite_id, orbit_number, start_time, max_elevation_time, max_elevation, end_time, duration, status, priority, created_at, updated_at)
    VALUES %s
    ON CONFLICT (satellite_id, orbit_number)
    DO UPDATE SET
        start_time = EXCLUDED.start_time,
        max_elevation_time = EXCLUDED.max_elevation_time,
        max_elevation = EXCLUDED.max_elevation,
        end_time = EXCLUDED.end_time,
        duration = EXCLUDED.duration,
        status = EXCLUDED.status,
        priority = EXCLUDED.priority,
        updated_at = EXCLUDED.updated_at
    """
    values = []
    for pasada in unique_pasadas:
        values.append((
            str(uuid.uuid4()),
            pasada.satellite_id,
            pasada.orbit_number,
            pasada.start_time,
            pasada.max_elevation_time,
            float(pasada.max_elevation),
            pasada.end_time,
            pasada.duration,
            pasada.status.value,
            pasada.priority.value,
            datetime.now(),
            datetime.now()
        ))
    with conn.cursor() as cur:
        execute_values(cur, sql, values, template=None, page_size=100)
    conn.commit()


def save_tle_data(conn, tle: TleData):
    with conn.cursor() as cur:
        query = """
        INSERT INTO tle_data (id, satellite_id, line1, line2, epoch, source, is_valid, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
        """
        cur.execute(query, (
            tle.id,
            tle.satellite_id,
            tle.line1,
            tle.line2,
            tle.epoch,
            tle.source,
            tle.is_valid,
            tle.created_at,
        ))
        conn.commit()


def get_ground_station_config(conn, station_name: str = "Estación Córdoba"):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT gsc.default_propagation_hours, gsc.night_start_hour, gsc.night_end_hour
            FROM ground_stations gs
            JOIN ground_station_configurations gsc ON gs.id = gsc.ground_station_id
            WHERE gs.name = %s AND gs.is_active = TRUE
            LIMIT 1
        """, (station_name,))
        row = cur.fetchone()
    if row:
        return {
            'default_propagation_hours': row[0],
            'night_start_hour': row[1],
            'night_end_hour': row[2]
        }
    else:
        return {
            'default_propagation_hours': 24,
            'night_start_hour': 20,
            'night_end_hour': 6
        }


def get_satellite_by_id(conn, satellite_id: str):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, name, priority_level, description,
                is_active, can_propagate, allow_daytime_propagation, allow_nighttime_propagation,
                min_elevation, max_elevation
            FROM satellites
            WHERE id = %s
            LIMIT 1
        """, (satellite_id,))
        row = cur.fetchone()

    if not row:
        return None

    return {
        'id': row[0],
        'name': row[1],
        'priority_level': row[2],
        'description': row[3],
        'is_active': row[4],
        'can_propagate': row[5],
        'allow_daytime_propagation': row[6],
        'allow_nighttime_propagation': row[7],
        'min_elevation': float(row[8]) if row[8] is not None else None,
        'max_elevation': float(row[9]) if row[9] is not None else None,
    }


def get_station_coordinates(conn, station_name: str = "Estación Córdoba"):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT latitude, longitude, altitude
            FROM ground_stations
            WHERE name = %s AND is_active = TRUE
            LIMIT 1
        """, (station_name,))
        row = cur.fetchone()

    if row:
        lat, lon, alt = float(row[0]), float(row[1]), float(row[2])
        return lat, lon, alt
    else:
        raise Exception("No se encontró la estación activa.")
