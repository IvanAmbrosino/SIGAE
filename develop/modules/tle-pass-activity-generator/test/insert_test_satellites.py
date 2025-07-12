import psycopg2
from datetime import datetime

db_config = {
    'dbname': 'planificacion_satelital',
    'user': 'planificador_app',
    'password': 'SecurePassword123!',
    'host': 'satplan_db',
    'port': 5432
}

SATELLITES = [
    {
        'name': 'ISS',
        'norad_id': '25544',
        'priority_level': 'high',
        'description': 'Estación Espacial Internacional'
    },
    {
        'name': 'AQUA',
        'norad_id': '27424',
        'priority_level': 'medium',
        'description': 'Satélite de observación de la NASA'
    },
    {
        'name': 'LANDSAT-8',
        'norad_id': '39084',
        'priority_level': 'critical',
        'description': 'Satélite de observación terrestre'
    }
]

def insert_satellites():
    try:
        conn = psycopg2.connect(**db_config)
        with conn.cursor() as cur:
            for sat in SATELLITES:
                cur.execute("""
                    INSERT INTO satellites (id, name, priority_level, description, is_active, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (
                    sat['norad_id'],       # Usamos NORAD ID como PK (id)
                    sat['name'],
                    sat['priority_level'],
                    sat['description'],
                    True,
                    datetime.now(),
                    datetime.now()
                ))
        conn.commit()
        print("Satélites de prueba insertados.")
    except Exception as e:
        print("Error al insertar satélites:", e)
    finally:
        conn.close()

if __name__ == "__main__":
    insert_satellites()
