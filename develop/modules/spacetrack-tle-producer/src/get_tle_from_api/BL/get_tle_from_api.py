from datetime import datetime, timezone, timedelta
from get_tle import GetTleSpaceTrack
from post_tle import PostTle
from DAL_tle.conexionBD import obtener_listado_satelites
from Helpers.tle_antiguo import tle_antiguo # type: ignore
from Helpers.crc_validation import validate_tle_checksum
import logging
from config_manager import ConfigManager
from logs.logger import load_logger

from confluent_kafka import Producer
import logging.handlers
import logging

logger = logging.getLogger("GestorTLE")


class GestorTLE:
    """Gestor para obtener TLEs de una lista de satélites"""
    def __init__(self, tmp_dir: str = "tmp"):
        print("Inicializando GestorTLE...")
        load_logger(self)
        self.tle_getter = GetTleSpaceTrack(tmp_dir, logger)
        self.config = ConfigManager().config
        self.kafka_config = self.config["kafka_config"]
        self.kafka_producer = PostTle(logger) # Enviar mensajes al tópico TLE de Kafka
        self.kafka_topic = "TLE"


        tles = self.obtener_tles()
        if not tles:
            logger.error("No se obtuvieron TLEs de la API.")
            return
        logger.info(f"Obtenidos {len(tles)} TLEs de la API.")
        logger.debug(tles)
        self.validar_y_enviar_tles(tles)

    def obtener_tles(self): #de la API de SpaceTrack
        satelites = obtener_listado_satelites()
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

            print(line1)
            if not validate_tle_checksum(line1) or not validate_tle_checksum(line2):
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
        "timestamp": ts_iso
        }
        
        logger.debug(f"Mensaje TLE generado: {mensaje_tle}")
        return mensaje_tle

    