"""Module for Viasat Antenna Adapter."""
import os
import logging
import logging.handlers

from infraestructure.sqlite_manager import SQLiteManager # pylint: disable=import-error
from infraestructure.config_manager import ConfigManager # pylint: disable=import-error
from infraestructure.kafka_adapter import KafkaConnector # pylint: disable=import-error
from application.message_manager import MessageManager # pylint: disable=import-error

logger = logging.getLogger("Main")

class AntenaAdapter:
    """Main class for the Viasat Antenna Adapter."""
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()              # Se cargan las configuracioens

        self.script_dir = os.path.dirname(os.path.abspath(__file__)) # Directory of the script
        self.logs_config = self.config['logs']                       # Logging configuration
        kafka_config = self.config['kafka']                          # Kafka connection configuration
        self.load_logger()                                           # Carga la configuracion de los logs

        self.kafka_adapter = KafkaConnector(kafka_config, logger)
        self.process_message = MessageManager(logger)

        # Inicializacion del modulo
        SQLiteManager().inicializar() # Inicianlizacion de la base de datos (en caso que no exista)

        for message, message_value in self.kafka_adapter.get_message():
            self.process_message.process_message(message_value)
            self.kafka_adapter.commmit_message(message)

    def load_logger(self) -> None:
        """Load logger configuration."""
        try:
            if not logger.handlers:
                if self.logs_config['log_level']:
                    logger.setLevel(self.logs_config['log_level'])
                else:
                    logger.setLevel(logging.INFO)
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
