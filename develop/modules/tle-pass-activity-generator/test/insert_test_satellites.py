import psycopg2
from datetime import datetime
import yaml

def load_config():
    with open('configs/config.yaml', 'r') as f:
        return yaml.safe_load(f)
    
    
SATELLITES = [
    {
        'name': 'ISS',
        'norad_id': '25544',
        'priority_level': 'high',
        'description': 'Estación Espacial Internacional',
        'is_active': True,
        'can_propagate': True,
        'propagate_day': True,
        'propagate_night': True,
        'min_elevation': 10.0,
        'max_elevation': 90.0
    },
    {
        'name': 'AQUA',
        'norad_id': '27424',
        'priority_level': 'medium',
        'description': 'Satélite de observación de la NASA',
        'is_active': True,
        'can_propagate': True,
        'propagate_day': False,
        'propagate_night': True,
        'min_elevation': 15.0,
        'max_elevation': 85.0
    },
    {
        'name': 'LANDSAT-8',
        'norad_id': '39084',
        'priority_level': 'critical',
        'description': 'Satélite de observación terrestre',
        'is_active': True,
        'can_propagate': True,
        'propagate_day': True,
        'propagate_night': False,
        'min_elevation': 20.0,
        'max_elevation': 88.0
    }
]


def insert_satellites():
    config = load_config()
    db_config = config['database']
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
