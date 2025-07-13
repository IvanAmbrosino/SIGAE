import psycopg2
from psycopg2.extras import execute_values
from contextlib import contextmanager
from datetime import datetime
import uuid 

from domain.tle_pass import TleData


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

def save_pass_activities(conn, pasadas):
    sql = """
    INSERT INTO activities
    (id, satellite_id, orbit_number, start_time, max_elevation_time, end_time, duration, status, priority, created_at, updated_at)
    VALUES %s
    ON CONFLICT (satellite_id, orbit_number)
    DO UPDATE SET
        start_time = EXCLUDED.start_time,
        max_elevation_time = EXCLUDED.max_elevation_time,
        end_time = EXCLUDED.end_time,
        duration = EXCLUDED.duration,
        status = EXCLUDED.status,
        priority = EXCLUDED.priority,
        updated_at = EXCLUDED.updated_at
    """
    values = []
    for pasada in pasadas:
        values.append((
            str(uuid.uuid4()),
            pasada.satellite_id,  # ← ahora es el norad_id
            pasada.orbit_number,
            pasada.start_time,
            pasada.max_elevation_time,
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
        if cur.rowcount == 1:
            print(f"[INFO] TLE guardado: {tle.satellite_id} - {tle.epoch}")
        else:
            print(f"[INFO] TLE duplicado no insertado: {tle.satellite_id} - {tle.epoch}")