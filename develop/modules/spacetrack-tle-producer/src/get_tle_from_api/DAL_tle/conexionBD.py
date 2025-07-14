import psycopg2
import yaml


def load_config():
    with open('configs/config.yaml', 'r') as f:
        return yaml.safe_load(f)
    
def obtener_listado_satelites() -> list[dict]:
        config = load_config()
        conn = psycopg2.connect(config)
        with conn.cursor() as cur:
            cur.execute("SELECT norad_id FROM satellites WHERE get_from_api = TRUE;")
            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]
        conn.close()
        print("Resultados de BD:", results)
        return results