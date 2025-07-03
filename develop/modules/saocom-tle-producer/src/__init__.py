"""Modulo que se encarga de obtener el ultimo TLE de los satelites SAOCOM en el MOC"""
# Luego verifica que sea correcto y el ultimo
#   - Para eso hay que verificar el formato del tle
#   - Verificar que el TLE sea el ultimo
#   - Verificar que el TLE no haya sido enviado antes
#   - Tener un listado de TLes enviados
# Envia el mensaje con el nuevo TLE a kafka por el topic del NoradID del satelite
import os
import re
import logging
import logging.handlers
from datetime import datetime, timedelta
from time import sleep
from config_manager import ConfigManager
from get_tle import GetTleSaocomSftp
from post_tle import PostTle
from mail_notification import SendNotification

logger = logging.getLogger("Main")

class SaocomTlePublisher:
    """Clase que obtiene el TLE de los satelites SAOCOM en el MOC"""
    def __init__(self,config : dict):
        self.tmp_dir            = os.path.dirname(os.path.abspath(__file__)) + '/tmp'
        self.script_dir         = os.path.dirname(os.path.abspath(__file__))
        self.config             = config
        self.satellite_config   = self.config["satellite_config"]
        self.logs_config        = self.config["logs"]
        self.mail_config        = self.config["mail"]
        self.get_tle            = GetTleSaocomSftp(self.tmp_dir,logger=logger)
        self.post_tle           = PostTle(logger=logger)
        self.mail_notification  = SendNotification()
        self.load_logger()

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

    def send_mail(self, tle, msg):
        """Encargada de llamar la funcion de envio de mail"""
        if self.mail_config["notifications"]:
            self.mail_notification.run(mail_config= self.mail_config,
                                    tle = tle, msg= msg)

    def validate_tle_checksum(self, tle_line) -> bool:
        """
        Verifica el checksum de una línea TLE (Line 1 o Line 2).
            - Números (0 al 9): se suman directamente.
            - Guiones (-): cuentan como 1.
        Retorna True si el checksum es válido.
        """
        if len(tle_line) < 69:
            return False
        line_data = tle_line[:68]
        expected_checksum = int(tle_line[68])

        total = 0
        for char in line_data:
            if char.isdigit():
                total += int(char)
            elif char == '-':
                total += 1
        return total % 10 == expected_checksum

    def validate_tle_format(self, tle : dict) -> bool:
        """Verifica el formato del TLE y el CRC"""
        satellite_name = self.satellite_config["satellite_altername"] if self.satellite_config["satellite_altername"] else self.satellite_config["satellite_name"]
        try:
            if tle['satellite_name'] == satellite_name and len(tle['line1']) == 69 and len(tle['line2']) == 69:
                logger.debug("Cantidad de caracteres Validada = OK")
                if self.validate_tle_checksum(tle['line1']) and self.validate_tle_checksum(tle['line2']):
                    logger.debug("CRC Validado = OK")
                    return True
            self.send_mail(tle,"Validacion de formato y CRC fallida")
            logger.debug("Error al validar ek formato y CRC, el json es incorrecto %s",tle)
        except KeyError as e:
            logger.error("Error al validar, el json es incorrecto: %s",e)
        return False

    def tle_epoch_to_datetime(self, epoch_str):
        """Funcion que convierte el epoch del tle a formato datetime"""
        logger.debug("epoch: %s",epoch_str)
        pattern = r"^\d{5}\.\d{8}$"
        if re.fullmatch(pattern, epoch_str) is not None:
            year = int(epoch_str[:2])
            year += 2000 if int(epoch_str[:2]) < 57 else 1900  # Según norma NORAD
            day_of_year = float(epoch_str[2:])
            day_int = int(day_of_year)
            day_frac = day_of_year - day_int
            return datetime(year, 1, 1) + timedelta(days=day_int - 1, seconds=day_frac * 86400)

    def is_latest_tle(self, tle : dict, tle_type : str) -> bool:
        """Verifica que el TLE sea el ultimo"""
        file_tle_bkp = os.path.join(self.tmp_dir, f"{tle_type}_bkp.txt")
        if not os.path.exists(file_tle_bkp):
            with open(file_tle_bkp, "w", encoding='utf-8') as f:
                f.write("") # Creamos el archivo vacio
            logger.info("El archivo de backup no existe, se crea uno nuevo")

        with open(file_tle_bkp, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        if len(lines) >= 3:
            if (lines[1].strip() != tle['line1'] or lines[2].strip() != tle['line2']):
                logger.debug("El TLE es diferente al anterior. Lineas: %s TLE nuevo: %s", lines, tle)
                old_tle_date = self.tle_epoch_to_datetime(lines[1].strip().split()[3])
                new_tle_date = self.tle_epoch_to_datetime(tle['line1'].split()[3])
                if new_tle_date > old_tle_date:
                    logger.debug("Comparacion de Epoch Validado = OK")
                    return True
                self.send_mail(tle,"Comparacion con epoch Erronea")
                logger.debug("Comparacion de Epoch Validado = Err -> TLE con epoch menor al anterior")

        elif len(lines) == 0:
            logger.info("Es el primer TLE")
            return True

        return False

    def write_tle_bkp(self, tle : dict, tle_type : str) -> None:
        """Escribe el TLE en el backup"""
        file_tle_bkp = os.path.join(self.tmp_dir, f"{tle_type}_bkp.txt")
        with open(file_tle_bkp, 'w', encoding='utf-8') as f:
            f.write(f"{tle['satellite_name']}\n")
            f.write(f"{tle['line1']}\n")
            f.write(f"{tle['line2']}\n")

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

        for tle_type in self.satellite_config["type"]:
            new_tle = self.get_tle.get_tle(tle_type)
            if new_tle is not None:
                if self.validate_tle_format(new_tle):
                    if self.is_latest_tle(new_tle, tle_type):
                        self.write_tle_bkp(new_tle,tle_type) # Escribimos el nuevo TLE en el backup
                        logger.info("TLE Nuevo -> Actualuzando en las antenas")
                        logger.info( '\n'.join([f"{key}: {data}" for key, data in new_tle.items()]))
                        self.post_tle.kafka_producer(new_tle)
                    else:
                        logger.info("No hay cambios en el TLE para el satelite %s", new_tle['satellite_name'])
                else:
                    logger.error("El formato del TLE es incorrecto para el satelite %s", new_tle['satellite_name'])

        self.get_tle.close_sftp() # Cierra la conexion

if __name__ == "__main__":
    configs = ConfigManager().config
    saocom_tle_publisher = SaocomTlePublisher(config=configs)
    while True:
        try:
            saocom_tle_publisher.run()
        except Exception as e: # pylint: disable=broad-exception-caught
            logger.error("Error en el proceso principal: %s", e)
        finally:
            sleep(configs["sleep_time"])
