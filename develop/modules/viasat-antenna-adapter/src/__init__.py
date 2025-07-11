"""Module for Viasat Antenna Adapter."""
import os
import logging
import logging.handlers

from .infraestructure import kafka_adapter
from .application import process_message

logger = logging.getLogger("Main")

class AntenaAdapter:
    """Main class for the Viasat Antenna Adapter."""
    def __init__(self):
        self.antena_unit = "antvstf01"                               # Antenna unit name
        self.config_manager = ConfigManager().config                 # Configuration manager instance
        self.script_dir = os.path.dirname(os.path.abspath(__file__)) # Directory of the script
        self.logs_config = config['logs']                            # Logging configuration
        kafka_config = config['kafka_conn']                          # Kafka connection configuration
        self.load_logger()                                           # Carga la configuracion de los logs

        self.kafka_adapter = kafka_adapter.KafkaConnector(kafka_config, logger)
        self.process_message = process_message.ProcessMessage()

        messageTLE = { # Ejemplo de mensaje TLE
                "type": "tle",
                "satellite_name": "ISS (ZARYA)",
                "norad_id": "25544",
                "timestamp": "2025-07-11T10:30:00Z",
                "tle": {
                    "line1": "1 25544U 98067A   25191.52851852  .00001264  00000-0  32801-4 0  9993",
                    "line2": "2 25544  51.6427 307.4972 0004831  62.0716  63.4589 15.50296030399999"
                }
        }

        messagePlan = { # Ejemplo de mensaje de planificacion
            "type": "plan",
            "antenna_id": "ANTENA_6",
            "timestamp": 1752270600000,
            "source": "planificador_automatico",
            "plan": [
                {
                "task_id": "SAOCOM1B_ANTENA_6_2025_193_130000",
                "satellite": "SAOCOM-1B",
                "action": "append",
                "norad_id": "46265",
                "config_id": 10,
                "time_window": {
                    "start": "2025-07-11T14:00:00Z",
                    "end": "2025-07-11T14:15:00Z"
                    },
                "prepass_seconds": 120,
                "postpass_seconds": 60,
                "metadata": {
                    "priority": "urgent",
                    }
                }
            ]
        }

        messagePlanTLE = { # Ejemplo de mensaje de planificacion con TLEs (planificaciones criticas)
            "type": "plan+tles",
            "antenna_id": "ANTENA_2",
            "timestamp": "2025-07-11T10:40:00Z", # Timestamp in ISO format
            "source": "planificador_automatico",
            "plann": [
                {
                "task_id": "SAOCOM1B_ANTENA_2_2025_193_130000",
                "satellite": "SAOCOM-1B",
                "action": "append",
                "norad_id": "25544",
                "time_window": {
                    "start": "2025-07-11T14:00:00Z",
                    "end": "2025-07-11T14:15:00Z"
                },
                "prepass_seconds": 120,
                "postpass_seconds": 60,
                "metadata": {
                    "priority": "urgent",
                }
                }
            ],
            "tles": [ # Se le añade la lista de TLEs
                {
                "norad_id": "25544",
                "timestamp": "2025-07-11T10:30:00Z",
                "tle": {
                    "line1": "1 25544U 98067A   25191.52851852  .00001264  00000-0  32801-4 0  9993",
                    "line2": "2 25544  51.6427 307.4972 0004831  62.0716  63.4589 15.50296030399999"
                }
                }
            ]
        }


        for message, message_value in self.kafka_adapter.get_messages():
            self.process_message()

    def load_logger(self) -> None:
        """Load logger configuration."""
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

if __name__ == "__main__":
    AntenaAdapter()
