"""Modulo que se encarga de obtener los ultimos TLEs de los satelites en el listado"""
# Luego verifica que sea correcto y el ultimo
#   - Para eso hay que verificar el formato del tle
#   - Verificar que el TLE sea el ultimo
#   - Verificar que el TLE no haya sido enviado antes
#   - Tener un listado de TLes enviados
# Envia el mensaje con el nuevo TLE a kafka por el topic del NoradID del satelite
import os
import random
import re
from time import sleep
import logging
import logging.handlers
from datetime import datetime, timedelta
from config_manager import ConfigManager
from get_tle import GetTleSpaceTrack
from post_tle import PostTle

logger = logging.getLogger("Main")

class SpaceTrackTlePublisher:
    """Clase que obtiene el TLE de los satelites"""
    def __init__(self,config : dict):
        self.script_dir         = os.path.dirname(os.path.abspath(__file__))
        self.tmp_dir            = self.script_dir + '/tmp'
        self.config_dir         = self.script_dir + '/configs'
        self.file_tle_bkp       = self.tmp_dir + "/list_TLEs_bkp.txt"
        self.config             = config
        self.logs_config        = self.config["logs"]
        self.list_config        = self.config["list_satelites"]
        self.get_tle            = GetTleSpaceTrack(self.tmp_dir,logger=logger)
        self.post_tle           = PostTle(logger=logger)
        self.list_satellites    = {} # Diccionario con los satelites
        self.tles               = {} # Diccionario con los TLEs
        self.tles_bkp           = {} # Diccionario con los TLEs de backup
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

    def get_list_satellites(self):
        """Obtiene el listado de satelites del archivo csv
        - Suponemos que la primera linea tiene los nombres de las columnas
        - Pasan 3 parametros:
            - 1. NoradID
            - 2. Nombre del satelite
            - 3. Nombre alternativo del satelite
        """
        #{          ESTRUCTURA DEL DICCIONARIO
        #"norad_id" : {
        #    "satellite_name":"name",
        #    "altername":"altername",
        #    "norad_id":"norad_id",
        #    },
        #}
        self.list_satellites = {}
        try:
            with open(self.config_dir + "/" + self.list_config["file"], 'r', encoding='utf-8') as f:
                lines = f.readlines()
            keys = lines[0].strip().split(self.list_config["separator"])
            for line in lines[1:]:
                values = line.strip().split(self.list_config["separator"])
                self.list_satellites[str(values[0])] = {}
                for i,key in enumerate(keys):
                    self.list_satellites[str(values[0])][key] = values[i]
        except FileNotFoundError as e:
            logger.error("Error al abrir el archivo de satelites. El archivo no existe: %s",e)
        except IndexError as e:
            logger.error("Error al leer el archivo de satelites: %s",e)


    def validate_tle_format(self, norad_id : str, tle : dict) -> bool:
        """Verifica el formato del TLE"""
        # El formato del TLE es el siguiente:
        # 1. Primera línea: 'name' -> Nombre del satélite reconocido por la antena
        # 2. Segunda línea: 'line1' -> NORAD ID del satélite y datos con 69 caracteres
        # 3. Tercera línea: 'line2' -> Datos del satélite con 69 caracteres
        if tle["satellite_name"] != self.list_satellites[norad_id]["ALTNAME"]:
            tle["satellite_name"] = self.list_satellites[norad_id]["ALTNAME"]
        try:
            if len(tle['line1']) == 69 and len(tle['line2']) == 69:
                return True
        except KeyError as e:
            logger.debug("Error al validar el formato del TLE: %s",tle)
            logger.error("Error al validar, el json es incorrecto: %s",e)
        return False

    def read_tles(self) -> dict:
        """Funcion que lee todos los tle del archivo tmp y los guarda en un diccionario"""
        with open(self.file_tle_bkp, "r",encoding='utf-8') as f:
            content = f.read()
        tle_entries = re.findall(r"(.*?)\n(1 .*?)\n(2 .*?)\n", content, re.MULTILINE) # Separa de a 3 lineas.
        self.tles_bkp = {entry[0].strip(): (entry[1], entry[2]) for entry in tle_entries} # Diccionario con key = nombre del satelite.
        logger.debug("TLEs leidos del archivo de configuracion: \n %s",self.tles_bkp)

    def write_tles(self) -> None:
        """Funcion que escribe todos los tles del diccionario en el archivo tmp"""
        with open(self.file_tle_bkp, "w",encoding='utf-8') as f:
            for name, (tle1, tle2) in self.tles_bkp.items():
                f.write(f"{name}\n{tle1}\n{tle2}\n")
        logger.info("Se escribieron %s TLEs en el archivo de backup", len(self.tles_bkp))

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

    def compare_new_tle(self,tle_new : dict, norad_id : str) -> bool:
        """
        Compara si es un nuevo tle con el archivo backup
        Verifica si el TLE nuevo es de una fecha posterior al TLE anterior
        En caso afirmativo, se actualiza y retorna True
        """
        if not os.path.exists(self.file_tle_bkp):
            with open(self.file_tle_bkp, "w", encoding='utf-8') as f:
                f.write("") # Creamos el archivo vacio
            logger.info("El archivo de backup no existe, se crea uno nuevo")

        self.read_tles() # Leemos los TLE del archivo BKP.
        found,updated = False,False
        logger.debug("<<<<<<<<<<<<<<<<<<<<< TLEs en el archivo BKP >>>>>>>>>>>>>>>>>>>>>>>")
        logger.debug(self.tles_bkp)

        for key, (tle1, tle2) in self.tles_bkp.items(): # Recorremos los tles del archivo BKP
            if key == tle_new["satellite_name"] and tle2.split()[1] == norad_id: # Verificamos que se encuentre en el listado
                found = True
                if (tle1 != tle_new["line1"] or tle2 != tle_new["line2"]): # Si lo encuentra y es diferente lo actualiza
                    old_tle_date = self.tle_epoch_to_datetime(tle1.strip().split()[3])
                    new_tle_date = self.tle_epoch_to_datetime(tle_new['line1'].split()[3])
                    if new_tle_date > old_tle_date:
                        logger.debug("Comparacion de Epoch Validado = OK")
                        self.tles_bkp[key] = (tle_new["line1"], tle_new["line2"]) # Actualiza solamente ese tle
                        logger.debug('TLE ANTERIOR:\n%s\n%s\n%s',key,tle1,tle2)
                        logger.debug('TLE ACTUALIZADO:\n%s\n%s\n%s\n',tle_new["satellite_name"],tle_new["line1"],tle_new["line2"])
                        updated = True
                    else:
                        logger.debug("Comparacion de Epoch Validado = Err -> TLE con epoch menor al anterior")
                        logger.debug('TLE ANTERIOR:\n%s\n%s\n%s',key,tle1,tle2)
                        logger.debug('TLE NUEVO:\n%s\n%s\n%s',tle_new["satellite_name"],tle_new["line1"],tle_new["line2"])
                        logger.info("El TLE nuevo tiene un epoch menor al anterior, no se actualiza")
                break

        if not found: # En el caso que entre un TLE que no se encuentre en la lista BKP se agrega.
            logger.info("TLE del satelite: %s no se encuentra en el archivo, agregando a la lista",tle_new['satellite_name'])
            self.tles_bkp[tle_new["satellite_name"]] = (tle_new["line1"], tle_new["line2"])
            updated = True

        if updated:
            self.write_tles() # Escribimos el nuevo TLE en el archivo BKP
        return updated

    def run(self) -> None:
        """
        Funcion principal que obtiene el TLE y lo valida
        Obtiene el listado de satelites del archivo csv
        Hace la consulta a SpaceTrack obteniendo el listado de cada uno de los TLEs
        Valida el formato del TLE para que coincida con lo que se espera en kafka
        Verifica que el TLE sea diferente al anterior y el Ultimo
        Finalmente envia el mensaje a kafka
        """
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)

        self.get_list_satellites()
        logger.info("Espera aleatoria de %s segundos", self.config["interval"])
        sleep(random.randint(0,self.config["interval"])) # Esperamos un tiempo aleatorio para no hacer la consulta a SpaceTrack todos al mismo tiempo
        self.tles = self.get_tle.get_tles([ str(key) for key,_ in self.list_satellites.items()])
        logger.debug('listado tles: %s',self.tles)
        for norad_id, new_tle in self.tles.items():
            if new_tle is not None:
                if self.validate_tle_format(norad_id,new_tle):
                    if self.compare_new_tle(new_tle,norad_id):
                        logger.info("TLE Nuevo -> Enviando a Kafka \n%s",
                                    '\n'.join([f"{key}: {data}" for key, data in new_tle.items()]))
                        # En el archivo de config se especifica que topic name se tiene
                        topic = new_tle["satellite_name"].replace(" ","_") if self.config["topic_satellite_name"] else norad_id
                        self.post_tle.kafka_producer(new_tle, topic= topic)
                    else:
                        logger.info("No hay cambios en el TLE para el satelite %s, se mantiene el mismo",new_tle['satellite_name'])
                else:
                    logger.error("El formato del TLE para el satelite %s es incorrecto",new_tle['satellite_name'])

if __name__ == "__main__":
    while True:
        try:
            configs = ConfigManager().config
            saocom_tle_publisher = SpaceTrackTlePublisher(config=configs)
            saocom_tle_publisher.run()
        except Exception as e: # pylint: disable=broad-exception-caught
            # Con esta excepcion se atrapan todos los errores
            # Evita que el script consulte constantemente a SpaceTrack y se sature el sistema
            logger.error("Error en la ejecucion del script: %s", e)
        finally:
            logger.info("Esperando %s segundos para volver a ejecutar el script",
                        configs["sleep_time"])
            sleep(configs["sleep_time"])
