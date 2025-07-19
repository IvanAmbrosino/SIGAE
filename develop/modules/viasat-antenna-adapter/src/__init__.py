"""Module for Viasat Antenna Adapter."""
import os
import logging
import logging.handlers

from infraestructure.sqlite_manager import SQLiteManager # pylint: disable=import-error
from infraestructure.config_manager import ConfigManager # pylint: disable=import-error
from infraestructure.kafka_adapter import KafkaConnector # pylint: disable=import-error
from application.message_manager import MessageManager # pylint: disable=import-error
from domain.make_message import MakeMessages # pylint: disable=import-error

logger = logging.getLogger("Main")

class AntenaAdapter:
    """Main class for the Viasat Antenna Adapter."""
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()              # Se cargan las configuracioens
        self.plann_type = self.config['app']['message_types']['plan_type']
        self.plann_tle_type = self.config['app']['message_types']['plan_tle_type']

        self.script_dir = os.path.dirname(os.path.abspath(__file__)) # Directory of the script
        self.logs_config = self.config['logs']                       # Logging configuration
        self.kafka_config = self.config['kafka']                          # Kafka connection configuration
        self.load_logger()                                           # Carga la configuracion de los logs

        self.kafka_adapter = KafkaConnector(self.kafka_config, logger)
        self.process_message = MessageManager(logger)
        self.make_message = MakeMessages()

        # Inicializacion del modulo
        SQLiteManager().inicializar() # Inicianlizacion de la base de datos (en caso que no exista)

        for message, message_value in self.kafka_adapter.get_message():
            try:
                if self.process_message.process_message(message_value):
                    logger.debug("Mensaje procesado correctamente!!!")
                    if self.config['app']['send_ack'] and (message_value["message_type"] == self.plann_type or message_value["message_type"] == self.plann_tle_type):
                        for task in message.get('plan', []): # Si es planificacion y se encuentra habilitado, se envia el ACK
                            self.kafka_adapter.send_message(topic=self.kafka_config['ack_topic'], # Envia un ACK por cada Task
                                                            key=self.kafka_config['ack_topic'],
                                                            value=self.make_message.make_ack_message(task))
                logger.debug("Mensaje commiteado en kafka")
                self.kafka_adapter.commmit_message(message)
            except Exception as e: # pylint: disable=broad-exception-caught
                logger.error("Fatal error en el proceso principal: %s",e)

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
