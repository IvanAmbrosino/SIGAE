"""Modulo que se encarga de obtener TLEs de un inbox y enviarlos a kafka"""
import os
import logging
import logging.handlers
from time import sleep

from config_manager import ConfigManager
from check_tle import CheckTle
from get_tle import GetTleInbox
from post_tle import PostTle

logger = logging.getLogger("Main")

class InboxTleSender():
    """Clase que obtiene el TLE de un inbox y lo envia a kafka."""
    def __init__(self,config : dict):
        self.script_dir         = os.path.dirname(os.path.abspath(__file__))
        self.tmp_dir            = self.script_dir + '/tmp'
        self.config             = config
        self.logs_config        = self.config["logs"]
        self.mail_config        = self.config["mail"]
        self.load_logger()

        self.get_tle = GetTleInbox(self.tmp_dir, logger)
        self.check_tle = CheckTle(logger)
        self.post_tle = PostTle(logger)

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

    def run(self) -> None:
        """
        Funcion principal que obtiene el TLE y lo valida
        En este caso para los SAOCOM se recorren los Nominales y PPM
        Valida el formato del TLE para que coincida con lo que se espera en kafka
        Verifica que el TLE sea diferente al anterior y el Ultimo
        Finalmente envia el mensaje a kafka
        """
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)

        self.get_tle.connect_sftp() # Conecta al server sftp

        new_tle = self.get_tle.get_tle() # Obtiene el TLE del inbox
        if new_tle is not None:
            if self.check_tle.is_valid(new_tle):
                logger.info("TLE Nuevo -> Actualuzando en las antenas")
                logger.info( '\n'.join([f"{key}: {data}" for key, data in new_tle.items()]))
                self.post_tle.kafka_producer(new_tle)
            else:
                logger.error("El formato del TLE es incorrecto para el satelite %s", new_tle['satellite_name'])

        self.get_tle.close_sftp() # Cierra la conexion


if __name__ == "__main__":
    configs = ConfigManager().config
    if not configs:
        raise ValueError("No se pudo cargar la configuracion")
    inbox_tle_sender = InboxTleSender(configs)
    while True:
        try:
            inbox_tle_sender.run()
        except Exception as e: # pylint: disable=broad-exception-caught
            logger.error("Error en el proceso principal: %s", e)
        finally:
            sleep(configs["sleep_time"])
