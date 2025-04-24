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

logger = logging.getLogger("Main")

class Main():
    """Clase principal que tiene la secuencia de obtencion, formateo y carga de TLEs en las antenas"""
    def __init__(self):

        self.script_dir = os.path.dirname(os.path.abspath(__file__))       # Directorio del script
        tmp_dir = os.path.join(self.script_dir, 'tmp')                     # Directorio temporal para guardar los TLEs
        self.tmp_archive = os.path.join(tmp_dir, 'tle_tmp.txt')            # Archivo temporal para guardar los TLEs
        self.tmp_archive_bkp = os.path.join(tmp_dir, 'tle_bkp.txt')        # Archivo temporal backup para comparar si hay cambios
        config_dir = os.path.join(self.script_dir, 'configs')              # Directorio donde se ubican las configuraciones
        config_archive = os.path.join(config_dir, 'config.json')           # Archivo de configuracion
        self.post_tle = Connections(logger,self.script_dir)
        self.format_tle = FormatTle(logger)
        self.config_manager = ConfigManager()
        self.kafka_conector = KafkaConnector(config_archive,logger)
        self.config = self.config_manager.config                           # Configuracion general
        self.logs_config = self.config_manager.log_config                  # Configuracion de logs
        self.list_satellites = self.config_manager.load_satellites()       # Lista de satelites
        self.load_logger()                                                 # Carga la configuracion de los logs

        self.header = "n\n" if "viasat" in self.config["type"] else ""     # Setea el header del archivo

        #-----------------------------------------------------------------------------------------------------------------------------
        # Funcion principal que se encarga de obtener el TLE, formatearlo y mandarlo a las antenas
        # 1- Primero, al iniciar, obtiene todos los ultimos TLE y los envia
        #    Verifica si hay un archivo BKP, en caso que no lo haya o que sea diferente envia los TLE.
        #    Esto es para que ante el reinicio del contenedor, los TLE puedan ser cargados. (Forzar Actualizacion)
        #    Tambien ante la caida del servicio, que el ultimo mensaje no se pierda.

        # 2- Luego inicia el bucle de espera de mensajes, donde:
        #       - Al llegar un TLE, formatea el TLE
        #       - Arma el archivo con el formato correcto (DOS)
        #       - Actualiza el archivo BKP
        #       - Envia el archivo a la antena

        self.tles = []

        self.tles = self.kafka_conector.get_bulk_message(self.list_satellites,5) # Obtiene todos los TLE
        self.tles = [self.format_tle.format_tle(tle) for tle in self.tles] # Los formatea
        if self.update_new_tle(self.tles,self.header):
            self.make_tle_file(self.tles) # arma el archivo tmp
            self.post_tle.send_archive()

        self.tles = [] # Se limpia la lista de TLEs

        for get_tle in self.kafka_conector.get_message(self.list_satellites):
            if isinstance(get_tle,dict):
                format_tle = self.format_tle.format_tle(get_tle)
                self.tles.append(format_tle)

                if self.update_new_tle(self.tles,self.header):
                    self.make_tle_file(self.tles) # arma el archivo tmp
                    self.post_tle.send_archive()
                else:
                    for tle in self.tles:
                        logger.info("No hay cambios en el TLE %s",tle['name'])
                self.tles = [] # Se limpia la lista de TLEs

    def read_tles(self) -> dict:
        """Funcion que lee todos los tle del archivo tmp"""
        with open(self.tmp_archive_bkp, "r",encoding='utf-8') as f:
            content = f.read()
        tle_entries = re.findall(r"(.*?)\n(1 .*?)\n(2 .*?)\n", content, re.MULTILINE) # Separa de a 3 lineas.
        tles = {entry[0].strip(): (entry[1], entry[2]) for entry in tle_entries} #deuelve un diccionario con key = nombre del satelite.
        return tles

    def update_new_tle(self,list_tle,header) -> bool:
        """
        Compara si es un nuevo tle con el archivo backup
        En caso afirmativo, se actualiza y retorna True
        """
        list_tles_backup = self.read_tles() # Leemos los TLE del archivo BKP.
        updated = False
        for tle_new in list_tle:
            name = tle_new["name"].strip()
            norad_id = tle_new["line1"].split()[1]
            new_tle_line1, new_tle_line2 = tle_new["line1"], tle_new["line2"]
            found = False
            for key, (tle1, tle2) in list_tles_backup.items():
                if key == name and tle1.split()[1] == norad_id:
                    found = True
                    if (tle1 != new_tle_line1 or tle2 != new_tle_line2):
                        list_tles_backup[key] = (new_tle_line1, new_tle_line2) # Actualiza solamente ese tle
                        logger.info('TLE ANTERIOR:\n%s\n%s\n%s',key,tle1,tle2)
                        logger.info('TLE ACTUALIZADO:\n%s\n%s\n%s\n',name,new_tle_line1,new_tle_line2)
                        updated = True
                    break
            if not found: # En el caso que entre un TLE que no se encuentre en la lista BKP se agrega.
                list_tles_backup[name] = (new_tle_line1, new_tle_line2)
                updated = True

        if updated:
            with open(self.tmp_archive_bkp, "w",encoding='utf-8') as f:
                f.write(header)
                for name, (tle1, tle2) in list_tles_backup.items():
                    f.write(f"{name}\n{tle1}\n{tle2}\n")
        return updated

    def make_tle_file(self,list_tles) -> None:
        """Arma el archivo de TLEs para ser enviado a las antenas"""
        tle_string = self.header # Inicializa el string con el header
        with open(self.tmp_archive, "w", encoding='utf-8') as tle_file: # Se genera el archivo tmp con los TLEs
            for tle in list_tles:
                tle_string += "\n".join([tle["name"],tle["line1"],tle["line2"]]) + "\n"
            tle_file.write(tle_string)
        subprocess.run(["unix2dos", self.tmp_archive], check=True) # Se convierte en formato DOS

    def compare_tles(self) -> bool:
        """Compara el archivo generado con el nuevo, si hay alguna diferencia, se envia el nuevo a las antenas"""
        try:
            with open(self.tmp_archive, 'rb') as f1, open(self.tmp_archive_bkp, 'rb') as f2:
                return f1.read() == f2.read()
        except FileNotFoundError:
            return False

    def load_logger(self) -> None:
        """Load logger configuration."""
        try:
            if not logger.handlers:
                logger.setLevel(logging.INFO)
                handler = logging.handlers.RotatingFileHandler(
                    filename=(f'{self.script_dir}/{self.logs_config["logs"]["folder"]}/{self.logs_config["logs"]["filename"]}'),
                    mode='a', maxBytes=self.logs_config["logs"]["size"],
                    backupCount= self.logs_config["logs"]["rotation"],
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
