"""Module that make file the different types of messages"""
import logging
import subprocess
from time import sleep

from domain.validar_planificacion import ValidatePlann # pylint: disable=import-error
from domain.validar_planificacion import ValidateTLE # pylint: disable=import-error
from domain.make_file import MakeTLEFile # pylint: disable=import-error
from infraestructure.config_manager import ConfigManager # pylint: disable=import-error
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

    def send_tle_file(self) -> bool:
        """Envia el archivo tmp de tle creado a la antena"""
        local_archives =    ['/app/tmp/tmp_file_tle.txt',           '/app/tmp/tmp_file_tle.txt.done']
        remote_archives =   [self.config['tle_load_filename'],      f"{self.config['tle_load_filename']}.done"]
        if self.sender.send_files(local_archives, remote_archives):
            sleep(self.config['sleep_time'])
            if self.sender.get_file(self.config['tle_status_filename'],'/app/tmp/validate_tle.txt'):
                result = subprocess.run(["grep",self.config["accept_string"],'/app/tmp/validate.txt'],
                                        check=True, stdout=subprocess.PIPE
                                        ).stdout.decode().strip()
                self.logger.debug("Stdout: %s",result)
                self.logger.info("TLE cargado y aceptado correctamente")
                return True
        return False

    def send_plann_file(self) -> bool:
        """Envia el archivo tmp de plann creado a la antena"""
        local_archives =    ['/app/tmp/tmp_file_plann.xml',           '/app/tmp/tmp_file_plann.xml.done']
        remote_archives =   [self.config['planning_load_filename'],   f"{self.config['planning_load_filename']}.done"]
        if self.sender.send_files(local_archives, remote_archives):
            sleep(self.config['sleep_time'])
            if self.sender.get_file(self.config['planning_status_filename'],'/app/tmp/validate_tle.txt'):
                self.validate_result_planificacion('/app/tmp/validate_tle.txt')
                return True
        return False

    def validate_result_planificacion(self, arhive_validate):
        """Valida los mensajes retornados de la antena al cargar la planificacion"""
        with open(arhive_validate, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for line in lines:
            if "INFO" in line:
                self.logger.info("[INFO MESSAGE] %s",line)
            elif "WARNING" in line:
                self.logger.warning("[WARNING MESSAGE] %s",line)
            elif "ERROR" in line:
                self.logger.error("[ERROR MESSAGE] %s",line)

    def process_message(self, msg: dict) -> bool:
        """Procesa los mensajes recibidos de Kafka y determina su tipo para poder ser procesado."""
        if msg["type"] == "TLE":
            if ValidateTLE().validate(msg): # Valida si necesito el TLE y sus valores
                mtf = MakeTLEFile()         # Inicializo la clase para crear el archivo TLE
                mtf.make_file_to_send(msg)  # Armo el archivo a enviar a la antena
                if self.send_tle_file():    # Envio el archivo a la antena
                    mtf.remove_tmp_files()  # Limpio el directorio /tmp
                    return True             # Aviso de llegada correcta del TLE a la antena
            return False
        elif msg["type"] == "plan":
            if ValidatePlann().validate(msg): # Valida si necesito el TLE y sus valores
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
