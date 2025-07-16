from datetime import datetime, timezone, timedelta

from post_tle import PostTle
from utils.tle_antiguo import tle_antiguo
from utils.crc_validation import validate_tle_checksum
from utils.logger import load_logger
from utils.ultimos_tles import get_last_tles
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
        
        self.config = ConfigManager().config
        self.kafka_config = self.config["kafka_config"]
        self.kafka_producer = PostTle(logger) # Enviar mensajes al tópico TLE de Kafka
        self.kafka_topic = "TLE"

        satelites = obtener_listado_satelites()
        if not satelites:
            print("No se encontraron satélites para obtener TLEs.")
            return

        ultimos_tles_satelites = get_last_tles(satelites, logger)
        if not ultimos_tles_satelites:
            print("No se encontraron TLEs anteriores en la base de datos.")
            return

        tles = obtener_tles(satelites, logger)
        if not tles:
            print("No se obtuvieron TLEs de la API.")
            return
        print(f"Obtenidos {len(tles)} TLEs de la API.")
        print(tles)
        self.validar_y_enviar_tles(tles, ultimos_tles_satelites)

    

    def validar_y_enviar_tles(self, tles: dict, ultimos_tles: list[dict]):
        ultimos_tles.sort(key=lambda x: "satellite_id")
        print("ultimos tles:", ultimos_tles)
        for norad_id, tle in tles.items():
            line1 = tle["line1"]
            line2 = tle["line2"]
            timestamp = tle["timestamp"]

            if not validate_tle_checksum(line1) or not validate_tle_checksum(line2):
                print(f"TLE con NoradID {norad_id} tiene CRC inválido.")
                return
            print(f"TLE con NoradID {norad_id} tiene CRC válido.")

            ultimo_sat_tle = None
            for u in ultimos_tles:
                if u["satellite_id"] == str(norad_id):
                    if ultimo_sat_tle is None:
                        ultimo_sat_tle = u
                        continue
                    elif datetime.fromisoformat(ultimo_sat_tle["epoch"]) < datetime.fromisoformat(u["epoch"]):
                        ultimo_sat_tle = u

            if ultimo_sat_tle is None:
                print(f"No se encontró TLE anterior para NoradID {norad_id}. Enviando nuevo TLE.")
            else:
                print("sat_tle mas reciente:", ultimo_sat_tle)

            st = datetime.fromisoformat(ultimo_sat_tle["epoch"]).replace(tzinfo=timezone.utc).timestamp() * 1000
            print('times:', timestamp, '| contra:', st)
            if tle_antiguo(timestamp, st):
                print(f"TLE con NoradID {norad_id} es antiguo a lo ya enviado.")
                return

            print(f"Enviando TLE válido para NoradID {norad_id} a Kafka.")

            tle_message = self.generar_mensaje_tle(tle, norad_id)

            # self.kafka_producer.kafka_producer(tle_message, self.kafka_topic)

            

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
        
        print(f"Mensaje TLE generado: {mensaje_tle}")
        return mensaje_tle

# if __name__ == "__main__":
#     algo = [{'xxx':'yyy'}]
#     print(algo[0]["xxx"])