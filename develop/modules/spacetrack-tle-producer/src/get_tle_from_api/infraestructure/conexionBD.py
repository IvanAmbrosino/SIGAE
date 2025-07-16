import psycopg2
import json


def load_config():
    with open('configs/config.json', 'r') as f:
        return json.load(f)
    
def obtener_listado_satelites() -> list[dict]:
        config = load_config()
        db_config = config["database"]
        conn = psycopg2.connect(**db_config)
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM satellites WHERE can_fetch_from_api = TRUE;")
            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]
        conn.close()
        print("Resultados de BD:", results)
        return results