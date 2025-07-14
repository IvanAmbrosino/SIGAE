"""Module that make file the different types of messages"""
import logging
from time import sleep

from infraestructure.config_manager import ConfigManager # pylint: disable=import-error
from domain.validar_planificacion import ValidatePlann # pylint: disable=import-error
from domain.validar_planificacion import ValidateTLE # pylint: disable=import-error
from domain.make_file import MakeTLEFile # pylint: disable=import-error
from infraestructure.antenna_connections import SFTPTunnel # pylint: disable=import-error
from infraestructure.antenna_connections import SFTPDirect # pylint: disable=import-error
from infraestructure.antenna_connections import SFTPDobleTunnel # pylint: disable=import-error


class MessageManager:
    """Clase para procesar mensajes entrantes de Kafka."""
    def __init__(self,logger: logging):
        self.logger = logger
        self.config = ConfigManager().load_config()

        if self.config["connection_method"] == "direct":
            self.sender = SFTPDirect()
        elif self.config["connection_method"] == "tunnel":
            self.sender = SFTPTunnel()
        elif self.config["connection_method"] == "double_tunnel":
            self.sender = SFTPDobleTunnel()
        else:
            self.logger.error("No se especificó ningun metodo de conexion: %s",self.config["connection_method"])

    def send_tle_file(self):
        """Envia el archivo tmp creado a la antena"""
        local_archives =    ['/app/tmp/tmp_file_tle.txt',   '/app/tmp/tmp_file_tle.txt.done']
        remote_archives =   [self.config['filename'],       f"{self.config['filename']}.done"]
        if self.sender.send_files(local_archives, remote_archives):
            sleep(self.config['sleep_time'])
            if self.sender.get_file()

    def process_message(self, msg: dict, ):
        """Procesa los mensajes recibidos de Kafka y determina su tipo para poder ser procesado."""
        if msg["type"] == "TLE":
            if ValidateTLE().validate(msg):
                # Validar si es para la antena - En caso contrario corta el proceso
                # Validar el CRC, epoch contra fecha actual, etc.
                # Validar si es mas nuevo que el ultimo TLE - Comparar en la BD (en caso contrario no lo procesa)
                MakeTLEFile().make_file_to_send(msg)
                self.send_tle_file()
        elif msg["type"] == "plan":
            #validar_plan(msg)
                # Validar si es para la antena - En caso contrario corta el proceso
                # Validar los horarios y que no se superponga con las otras planificaciones que estan en la BD
                # Validar que el satelite tenga TLE actualizado
                # Validar que la antena este disponible
            #save_plan_in_db(msg)
                # Guarda o actualiza la planificacion en la BD
            #make_plann_file(msg)
                # Validar que el archivo de planificacion este bien formado
            #send_plann_file(msg)
                # Envia el archivo de planificacion a la antena
                # Validar que el archivo sea Aceptado por la antena
                # Hace el commit del mensaje a kafka
            pass
        elif msg["type"] == "plan+tles":
            #validar_plan_con_tle(msg)
                # Validar si es para la antena - En caso contrario corta el proceso
                # Validar los horarios y que no se superponga con las otras planificaciones que estan en la BD
                # Validar que el satelite tenga TLE actualizado
                # Validar que la antena este disponible
            #make_tle_file(msg)
            #send_tle_file(msg) # primero debe enviar el TLE
            #make_plann_file(msg)
            #send_plann_file(msg)
            pass
