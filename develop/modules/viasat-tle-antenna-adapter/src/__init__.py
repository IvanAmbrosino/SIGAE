"""Modulo principal que tiene la secuencia de obtencion, formateo y carga de TLEs en las antenas"""
import os
import re
import subprocess
import logging
import logging.handlers

from config_manager import ConfigManager
from connections import Connections
from format_tle import FormatTle
from get_tle import KafkaConnector
from mail_notification import SendNotification

logger = logging.getLogger("Main")

class Main():
    """Clase principal que tiene la secuencia de obtencion, formateo y carga de TLEs en las antenas"""
    def __init__(self):

        self.config_manager     = ConfigManager()
        self.config             = self.config_manager.config               # Configuracion general
        self.logs_config        = self.config["logs"]                      # Configuracion de logs
        self.mail_config        = self.config["mail"]
        self.list_satellites    = self.config_manager.load_satellites()    # Lista de satelites

        self.script_dir         = os.path.dirname(os.path.abspath(__file__)) # Directorio del script
        tmp_dir                 = os.path.join(self.script_dir, 'tmp')       # Directorio temporal para guardar los TLEs
        self.tmp_archive        = os.path.join(tmp_dir, 'tle_tmp.txt')       # Archivo temporal para guardar los TLEs
        self.tmp_archive_bkp    = os.path.join(tmp_dir, 'tle_bkp.txt')       # Archivo temporal backup para comparar si hay cambios
        config_dir              = os.path.join(self.script_dir, 'configs')   # Directorio donde se ubican las configuraciones
        config_archive          = os.path.join(config_dir, 'config.json')    # Archivo de configuracion

        self.load_logger()                                                   # Carga la configuracion de los logs

        self.post_tle = Connections(logger,self.script_dir)
        self.format_tle = FormatTle(logger)
        self.kafka_conector = KafkaConnector(config_archive,logger,self.list_satellites)
        self.mail_notification  = SendNotification()

        self.header = "n\n" if "viasat" in self.config["type"] else ""       # Setea el header del archivo

        #-----------------------------------------------------------------------------------------------------------------------------
        # Funcion principal que se encarga de obtener el TLE, formatearlo y mandarlo a las antenas
        # 1- inicia el bucle de espera de mensajes, donde:
        #       - Al llegar un TLE, formatea el TLE
        #       - Arma el archivo con el formato correcto (DOS)
        #       - Actualiza el archivo BKP
        #       - Envia el archivo a la antena
        #       - Hace el commit del mensaje a kafka
        #-----------------------------------------------------------------------------------------------------------------------------

        self.tles = [] # Se limpia la lista de TLEs

        for message, get_tle in self.kafka_conector.get_message():
            if isinstance(get_tle,dict):
                try:
                    format_tle = self.format_tle.format_tle(get_tle)
                    self.tles.append(format_tle)
                    if self.update_new_tle(self.tles,self.header):
                        self.make_tle_file(self.tles) # arma el archivo tmp
                        if self.post_tle.send_archive():
                            self.kafka_conector.commmit_message(message= message)
                        else:
                            logger.error("Error al enviar el archivo TLE a la antena")
                            self.send_mail(format_tle, "Error al enviar el archivo TLE a la antena")
                    else:
                        for tle in self.tles:
                            logger.info("No hay cambios en el TLE %s",tle['satellite_name'])
                    self.tles = [] # Se limpia la lista de TLEs
                except Exception as e: # pylint: disable=broad-exception-caught
                    logger.error("Error con la llegada del TLE: %s", e)
                    self.send_mail(get_tle, f"Error general en el script con la llegada de un nuevo TLE: \n{e}")

    def send_mail(self, tle, msg):
        """Encargada de llamar la funcion de envio de mail"""
        if self.mail_config["notifications"]:
            self.mail_notification.run(mail_config= self.mail_config,
                                    tle = tle, msg= msg)

    def read_tles(self) -> dict:
        """
        Funcion que lee todos los tle del archivo tmp.
        Luego retorna un diccionario con key = satellite_name y el contenido del TLE.
        {satellite_name: (tle_line-1, tle_line-2)}
        """
        with open(self.tmp_archive_bkp, "r",encoding='utf-8') as f:
            content = f.read()
        tle_entries = re.findall(r"(.*?)\n(1 .*?)\n(2 .*?)\n", content, re.MULTILINE)
        tles = {entry[0].strip(): (entry[1], entry[2]) for entry in tle_entries}
        return tles

    def update_new_tle(self,list_tle,header) -> bool:
        """
        Compara si es un nuevo tle con el archivo backup que contiene el listado
        - En caso que sea diferente, se actualiza en el archivo y retorna True
        - En caso que no se encuentre en la lista, se agrega y retorna true
        """
        if not os.path.exists(self.tmp_archive_bkp):
            with open(self.tmp_archive_bkp, "w", encoding='utf-8') as f:
                f.write("") # Creamos el archivo vacio
            logger.info("El archivo de backup no existe, se crea uno nuevo")

        list_tles_backup = self.read_tles() # Leemos los TLE del archivo BKP.

        updated = False
        for tle_new in list_tle: # Para cada uno de los TLEs que llegaron
            found = False
            for key, (tle1, tle2) in list_tles_backup.items():
                # Si tienen los mismos nombres y norad_id
                if key == tle_new["satellite_name"] and tle2.split()[1] == tle_new["line2"].split()[1]:
                    found = True
                    if (tle1 != tle_new["line1"] or tle2 != tle_new["line2"]): # Si las lineas del TLE son diferentes
                        list_tles_backup[key] = (tle_new["line1"], tle_new["line2"]) # Actualiza el tle
                        logger.debug('TLE ANTERIOR:\n%s\n%s\n%s',key,tle1,tle2)
                        logger.info('NUEVO TLE:\n%s\n%s\n%s\n',tle_new["satellite_name"],tle_new["line1"],tle_new["line2"])
                        updated = True
                    break
            if not found: # En el caso que entre un TLE que no se encuentre en la lista BKP se agrega.
                list_tles_backup[tle_new["satellite_name"]] = (tle_new["line1"], tle_new["line2"])
                logger.debug("Nuevo satelite a la lista: %s",tle_new["satellite_name"])
                logger.debug("Tle: %s",(tle_new["line1"], tle_new["line2"]))
                updated = True

        if updated:
            with open(self.tmp_archive_bkp, "w",encoding='utf-8') as f:
                f.write(header)
                for name, (tle1, tle2) in list_tles_backup.items():
                    f.write(f"{name}\n{tle1}\n{tle2}\n")
            logger.debug('Archivo %s actualizado',self.tmp_archive)

        return updated

    def make_tle_file(self,list_tles) -> None:
        """
        Arma el archivo de TLEs para ser enviado a las antenas
        Solo arma el archivo para los TLE nuevos que llegaron
        """
        tle_string = self.header # Inicializa el string con el header
        with open(self.tmp_archive, "w", encoding='utf-8') as tle_file:
            for tle in list_tles:
                tle_string += "\n".join([tle["satellite_name"],tle["line1"],tle["line2"]]) + "\n"
            tle_file.write(tle_string)
        subprocess.run(["unix2dos", self.tmp_archive], check=True) # Se convierte en formato DOS

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
    Main()
