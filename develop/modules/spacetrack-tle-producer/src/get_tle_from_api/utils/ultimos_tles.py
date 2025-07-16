import psycopg2
import json

def load_config():
    with open('configs/config.json', 'r') as f:
        return json.load(f)

def get_last_tles(satelites, logger):
    """
    Obtiene los últimos TLEs de los satélites desde la base de datos.
    """
    print("Obteniendo últimos TLEs ...")
    config = load_config()
    db_config = config["database"]
    conn = psycopg2.connect(**db_config)
    
    with conn.cursor() as cur:
        cur.execute("SELECT satellite_id, epoch FROM tle_data WHERE id = ANY(%s);", ([s["id"] for s in satelites],))
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in cur.fetchall()]
    
    conn.close()
    
    print("Resultados de BD para epoch:", results) # HARCODEADO EL RESULTADO
    logger.info(f"Obtenidos {len(results)} últimos TLEs de la base de datos.")
    return [
 {
  "satellite_id": "25544",
  "epoch": "2024-07-03 04:25:30",
 },
 {
  "satellite_id": "27424",
  "epoch": "2024-07-03 04:59:59",
 },
 {
  "satellite_id": "39084",
  "epoch": "2024-07-03 04:50:52.8",
 },
 {
  "satellite_id": "25544",
  "epoch": "2024-07-03 04:33:36",
 },
 {
  "satellite_id": "27424",
  "epoch": "2024-07-03 05:02:24",
 }
]

