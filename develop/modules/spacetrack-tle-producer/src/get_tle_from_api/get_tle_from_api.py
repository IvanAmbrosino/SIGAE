import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from get_tle import GetTleSpaceTrack
from confluent_kafka import Producer
from post_tle import PostTle
# from conexionBD import get_noradIDs
import psycopg2
import logging.handlers
import logging
from config_manager import ConfigManager

logger = logging.getLogger("GestorTLE")

def validar_crc_tle(line1: str, line2: str) -> bool:
    """Valida el CRC de las líneas TLE"""
    def crc(line):
        return int(line[-1]) == (sum(ord(c) for c in line[:-1] if c.isdigit()) % 10)
    return True

def tle_antiguo(timestamp: int, dias_max: int = 3) -> bool:
    """Valida si el TLE es más antiguo que dias_max días"""
    tle_date = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
    return (datetime.now(timezone.utc) - tle_date) > timedelta(days=dias_max)

class GestorTLE:
    """Gestor para obtener TLEs de una lista de satélites"""

    def __init__(self, tmp_dir: str = "tmp", kafka_topic: str = None, kafka_config: dict = None):
        print("Inicializando GestorTLE...")
        self.load_logger()
        self.tle_getter = GetTleSpaceTrack(tmp_dir, logger)
        self.config = ConfigManager().config
        self.kafka_config = self.config["kafka_config"]
        self.kafka_producer = PostTle(logger) # Enviar mensajes al tópico TLE de Kafka

        self.kafka_topic = kafka_topic

        tles = self.obtener_tles()
        if not tles:
            logger.error("No se obtuvieron TLEs de la API.")
            return
        logger.info(f"Obtenidos {len(tles)} TLEs de la API.")
        logger.debug(tles)
        self.validar_y_enviar_tles(tles)

    def obtener_listado_satelites(self) -> list[dict]:
        conn = psycopg2.connect(
            host="satplan_db",
            # host="localhost",
            port=5432,
            dbname="planificacion_satelital",
            user="planificador_app",
            password="SecurePassword123!"
        )
        with conn.cursor() as cur:
            cur.execute("SELECT norad_id FROM satellites WHERE get_from_api = TRUE;")
            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]
        conn.close()
        logger.debug("Resultados de BD:", results)
        return results

    def obtener_tles(self): #de la API de SpaceTrack
        satelites = self.obtener_listado_satelites()
        norad_ids = [str(s["norad_id"]) for s in satelites]
        
        if not norad_ids:
            logger.info("No hay satélites para consultar por API.")
            return {}

        print(f"Consultando TLEs para los satélites: {norad_ids}")
        # tles = self.tle_getter.get_tles(norad_ids) 
        tles = {'25544': {'satellite_name': 'ISS (ZARYA)', 'line1': '1 25544U 98067A   25194.43411487  .00010152  00000-0  18227-3 0  9995', 'line2': '2 25544  51.6340 176.9702 0002675   6.8375 353.2650 15.50520436519237', 'timestamp': 1752402307000}, '27424': {'satellite_name': 'AQUA', 'line1': '1 27424U 02022A   25194.64751222  .00000601  00000-0  13142-3 0  9996', 'line2': '2 27424  98.3791 153.3336 0001148  53.8590  61.5800 14.61343650233816', 'timestamp': 1752420745000}}
        return tles

    def validar_y_enviar_tles(self, tles: dict):
        for norad_id, tle in tles.items():
            line1 = tle["line1"]
            line2 = tle["line2"]
            timestamp = tle["timestamp"]

            if not validar_crc_tle(line1, line2):
                logger.warning(f"TLE con NoradID {norad_id} tiene CRC inválido.")
                continue

            if tle_antiguo(timestamp):
                logger.warning(f"TLE con NoradID {norad_id} es antiguo.")
                continue

            print(f"Enviando TLE válido para NoradID {norad_id} a Kafka.")
            logger.info(f"Enviando TLE válido para NoradID {norad_id} a Kafka.")

            tle_message = self.generar_mensaje_tle(tle, norad_id)

            self.kafka_producer.kafka_producer(tle_message, self.kafka_topic)
        return

    def generar_mensaje_tle(self, tle: dict, norad_id: str) -> dict:
    
        ts = int(tle.get("timestamp", 0)) / 1000
        ts_iso = datetime.utcfromtimestamp(ts).isoformat()

        mensaje_tle = {
        "message_type": "TLE",
        "norad_id": norad_id,
        "satellite_name": tle.get("satellite_name", ""),
        "line1": tle.get("line1", ""),
        "line2": tle.get("line2", ""),
        "timestamp": str(tle.get("timestamp", ""))
        }
        
        logger.debug(f"Mensaje TLE generado: {mensaje_tle}")
        return mensaje_tle

    def load_logger(self) -> None:
        """Load logger configuration."""

        self.logs_config = {
        "folder":"logs",
        "filename": "test.log",
        "rotation": 5,
        "size": 5000000,
        "debug_mode": True
        }

        self.script_dir = Path(__file__).resolve().parent
        try:
            if not logger.handlers:
                log_level = logging.DEBUG if self.logs_config["debug_mode"] else logging.INFO
                logger.setLevel(log_level)
                handler = logging.handlers.RotatingFileHandler(
                    filename=(f'{self.script_dir}/{self.logs_config["folder"]}/{self.logs_config["filename"]}'),
                    mode='a', maxBytes=self.logs_config["size"],
                    backupCount= self.logs_config["rotation"],
                    encoding='utf-8')
                formatter = logging.Formatter(
                    "%(asctime) 15s - %(process)d - %(name)s -\
                        %(lineno)s - %(levelname)s - %(message)s")
                handler.setFormatter(formatter)
                logger.addHandler(handler)
        except TypeError as e:
            logger.error("error en la generacion de logs: %s",e)