"""Module for Viasat Antenna Adapter."""
import os
import logging
import logging.handlers

from .infraestructure import kafka_adapter, config_manager
from .application import message_manager


logger = logging.getLogger("Main")

class AntenaAdapter:
    """Main class for the Viasat Antenna Adapter."""
    def __init__(self):
        self.config_manager = config_manager.ConfigManager()
        self.config = 

        self.script_dir = os.path.dirname(os.path.abspath(__file__)) # Directory of the script
        self.logs_config = config['logs']                            # Logging configuration
        kafka_config = config['kafka_conn']                          # Kafka connection configuration
        self.load_logger()                                           # Carga la configuracion de los logs

        self.kafka_adapter = kafka_adapter.KafkaConnector(kafka_config, logger)
        self.process_message = message_manager.MessageManager(logger)


        for message, message_value in self.kafka_adapter.get_message():
            self.process_message.process_message(message_value)
            self.kafka_adapter.commmit_message(message)

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
