from datetime import datetime, timezone, timedelta
from get_tle import GetTleSpaceTrack
from post_tle import PostTle
from utils.tle_antiguo import tle_antiguo
from utils.crc_validation import validate_tle_checksum
from utils.logger import load_logger
from config_manager import ConfigManager
from infraestructure.conexionBD import obtener_listado_satelites
from infraestructure.get_API import obtener_tles

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

        satelites = obtener_listado_satelites()
        tles = obtener_tles(satelites)
        if not tles:
            logger.error("No se obtuvieron TLEs de la API.")
            return
        logger.info(f"Obtenidos {len(tles)} TLEs de la API.")
        logger.debug(tles)
        self.validar_y_enviar_tles(tles)

    

    def validar_y_enviar_tles(self, tles: dict):
        for norad_id, tle in tles.items():
            line1 = tle["line1"]
            line2 = tle["line2"]
            timestamp = tle["timestamp"]

            print(line1)
            if not validate_tle_checksum(line1) or not validate_tle_checksum(line2):
                logger.warning(f"TLE con NoradID {norad_id} tiene CRC inválido.")
                continue

            # if tle_antiguo(timestamp):
            #     logger.warning(f"TLE con NoradID {norad_id} es antiguo.")
            #     continue

            print(f"Enviando TLE válido para NoradID {norad_id} a Kafka.")
            logger.info(f"Enviando TLE válido para NoradID {norad_id} a Kafka.")

            tle_message = self.generar_mensaje_tle(tle, norad_id)

            self.kafka_producer.kafka_producer(tle_message, self.kafka_topic)

            

        return

    def generar_mensaje_tle(self, tle: dict, norad_id: str) -> dict:
    
        ts = int(tle.get("timestamp", 0)) / 1000
        ts_iso = datetime.utcfromtimestamp(ts).isoformat() + "Z"

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

    