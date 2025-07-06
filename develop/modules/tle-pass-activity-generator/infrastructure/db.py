import psycopg2
from psycopg2.extras import execute_values
from contextlib import contextmanager
from datetime import datetime
import uuid 

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

def get_satellite_id_by_name(conn, name):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM satellites WHERE name = %s", (name,))
        row = cur.fetchone()
        if row:
            return row[0]
        else:
            raise ValueError(f"Satellite with name '{name}' not found in DB")


def save_pass_activities(conn, pasadas):
    sql = """
    INSERT INTO activities
    (id, satellite_id, orbit_number, start_time, max_elevation_time, end_time, duration, status, priority, created_at, updated_at)
    VALUES %s
    """
    values = []
    for pasada in pasadas:
        # Obtener ID real desde el nombre
        satellite_uuid = get_satellite_id_by_name(conn, pasada.satellite_id)

        values.append((
            str(uuid.uuid4()),
            satellite_uuid,
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
        print("N columnas por fila:", len(values[0]))
        print("Primer fila:", values[0])
        execute_values(cur, sql, values, template=None, page_size=100)
    conn.commit()
