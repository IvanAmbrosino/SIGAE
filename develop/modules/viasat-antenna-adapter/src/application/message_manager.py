"""Module that make file the different types of messages"""
import logging
import subprocess
from time import sleep

from domain.validar_planificacion import ValidatePlann, ValidateTLE # pylint: disable=import-error
from domain.make_file import MakeTLEFile, MakePlannFile # pylint: disable=import-error
from infraestructure.config_manager import ConfigManager # pylint: disable=import-error
from infraestructure.antenna_connections import SFTPTunnel, SFTPDirect, SFTPDobleTunnel # pylint: disable=import-error
from infraestructure.sqlite_manager import SQLiteManager # pylint: disable=import-error


class MessageManager:
    """Clase para procesar mensajes entrantes de Kafka."""
    def __init__(self,logger: logging):
        self.logger = logger
        self.sqlite_manager = SQLiteManager()
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.send_config = self.config['send']
        self.app_config = self.config['app']
        self.files_config = self.config['files']
        self.server_config = self.send_config['server_config']

        if self.send_config["connection_method"] == "direct":
            server = self.send_config['server_config']
            self.sender = SFTPDirect(
                host=               server['host'],
                username=           server['username'],
                password=           self.config_manager.read_secret(server['password'])
            )
        elif self.send_config["connection_method"] == "tunnel":
            server = self.send_config['server_config']
            jump = self.send_config['jump_server']
            self.sender = SFTPTunnel(
                jump_host=          jump['host'],
                jump_user=          jump['username'],
                jump_password=      self.config_manager.read_secret(jump['password']),
                target_host=        server['host'],
                target_user=        server['username'],
                target_password=    self.config_manager.read_secret(server['password'])
            )
        elif self.send_config["connection_method"] == "double_tunnel":
            server = self.send_config['server_config']
            jump1 = self.send_config['jump_server']
            jump2 = self.send_config['second_jump_server']
            self.sender = SFTPDobleTunnel(
                jump1_host=         jump1['host'],
                jump1_user=         jump1['username'],
                jump1_password=     self.config_manager.read_secret(jump1['password']),
                jump2_host=         jump2['host'],
                jump2_user=         jump2['username'],
                jump2_password=     self.config_manager.read_secret(jump2['password']),
                target_host=        server['host'],
                target_user=        server['username'],
                target_password=    self.config_manager.read_secret(server['password'])
            )
        else:
            self.logger.error("No se especificó ningun metodo de conexion: %s",self.config["connection_method"])

    def send_tle_file(self) -> bool:
        """Envia el archivo tmp de tle creado a la antena"""
        local_archives =    ['/app/tmp/tmp_file.txt', '/app/tmp/tmp_file.txt.done']
        remote_archives =   [f"{ self.server_config['destination_path']}/{self.files_config['tle_load_filename']}",
                             f"{ self.server_config['destination_path']}/{self.files_config['tle_load_filename']}.done"]
        self.logger.debug("Listado de archivos locales: %s",local_archives)
        self.logger.debug("Listado de archivos remotos: %s",remote_archives)
        if self.sender.send_files(local_archives, remote_archives):
            self.logger.debug("Archivo enviado a la antena")
            self.logger.debug("Sleep de %s segundos",self.send_config['sleep_time'])
            sleep(self.send_config['sleep_time'])
            if self.sender.get_file(f"{ self.server_config['destination_path']}/{self.files_config['tle_status_filename']}",
                                    '/app/tmp/validate_tle.txt'):
                result = subprocess.run(["grep",self.files_config["accept_string"],'/app/tmp/validate.txt'],
                                        check=True, stdout=subprocess.PIPE
                                        ).stdout.decode().strip()
                self.logger.debug("Stdout: %s",result)
                self.logger.info("TLE cargado y aceptado correctamente")
                return True
            self.logger.error("No se pudo obtener el mensaje de status proveniente de la antena")
        return False

    def send_plann_file(self) -> bool:
        """Envia el archivo tmp de plann creado a la antena"""
        local_archives =    ['/app/tmp/tmp_file.xml', '/app/tmp/tmp_file.xml.done']
        remote_archives =   [f"{ self.server_config['destination_path']}/{self.files_config['planning_load_filename']}",
                             f"{ self.server_config['destination_path']}/{self.files_config['planning_load_filename']}.done"]
        self.logger.debug("Listado de archivos locales: %s",local_archives)
        self.logger.debug("Listado de archivos remotos: %s",remote_archives)
        if self.sender.send_files(local_archives, remote_archives):
            self.logger.debug("Archivo enviado a la antena")
            self.logger.debug("Sleep de %s segundos",self.send_config['sleep_time'])
            sleep(self.send_config['sleep_time'])
            if self.sender.get_file(f"{ self.server_config['destination_path']}/{self.files_config['planning_status_filename']}",
                                    '/app/tmp/validate_tle.txt'):
                result = subprocess.run(["grep",self.files_config["accept_string"],'/app/tmp/validate.txt'],
                                        check=True, stdout=subprocess.PIPE
                                        ).stdout.decode().strip()
                self.logger.debug("Stdout: %s",result)
                self.logger.info("TLE cargado y aceptado correctamente")
                return True
            self.logger.error("No se pudo obtener el mensaje de status proveniente de la antena")
        return False

    def save_plann_in_db(self, message: dict) -> None:
        """Funcion que guarda o modifica todas las pasadas en el cache"""
        for task in message['plan']:
            if task['action'] == 'ADD':
                self.sqlite_manager.upsert_planificacion(task) # INSERT
            elif task['action'] == 'CANCEL':
                self.sqlite_manager.delete_activity_by_id(task['task_id']) # DELETE WHERE
            elif task['action'] == 'PURGE':
                self.sqlite_manager.purge_activities() # DELETE ALL
            else:
                self.logger.warning("Accion no reconocida para el guardado en la BD: %s",task['action'])

    def process_message(self, msg: dict) -> bool:
        """Procesa los mensajes recibidos de Kafka y determina su tipo para poder ser procesado."""
        if msg["message_type"] == "TLE":
            if ValidateTLE(self.logger).validate(msg,chequeo= self.app_config['broadcast_tle']): # Valida si necesito el TLE y sus valores
                mtf = MakeTLEFile()                                               # Inicializo la clase para crear el archivo TLE
                mtf.make_file_to_send(msg)                                        # Armo el archivo a enviar a la antena
                if self.send_tle_file():                                          # Envio el archivo a la antena
                    mtf.remove_tmp_files()                                        # Limpio el directorio /tmp
                    return True                                                   # Aviso de llegada correcta del TLE a la antena  -> Commit en Kafka
                self.logger.error("Error al enviar el archivo de TLE")
            return False
        elif msg["message_type"] == "PLANN":
            if ValidatePlann(self.logger).validate(msg): # Valida la planificacion
                mpf = MakePlannFile()           # Inicializo la clase para crear el archivo TLE
                mpf.make_file_to_send(msg)      # Armo el archivo a enviar a la antena
                if self.send_plann_file():      # Validar que el archivo de planificacion este bien formado
                    mpf.remove_tmp_files()      # Limpio el directorio /tmp
                    self.save_plann_in_db(msg)  # Guarda o actualiza la planificacion en la BD
                    return True                 # Aviso de llegada correcta de la Planificacion a la antena -> Commit en Kafka
                self.logger.error("Error al enviar el archivo de Planificación")
            return False
        elif msg["message_type"] == "PLANNTLE":
            if ValidateTLE(self.logger).validate(msg, chequeo= False):         # Valida el TLE. sin el chequeo de que tiene planificacion
                if ValidatePlann(self.logger).validate(msg, chequeo= False):   # Valida la planificacion, sin el chequeo de que tiene tle
                    mtf = MakeTLEFile()
                    mtf.make_file_to_send(msg)                      # Primero armo y envio el TLE
                    if self.send_tle_file():
                        mtf.remove_tmp_files()
                    mpf = MakePlannFile()
                    mpf.make_file_to_send(msg)                      # Segundo armo y envio la Planificacion
                    if self.send_plann_file():
                        mpf.remove_tmp_files()
