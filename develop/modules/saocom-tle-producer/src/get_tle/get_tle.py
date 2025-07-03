"""Busca el TLE de los satelites SAOCOM en el MOC"""
import os
import gzip
import logging
import paramiko
from config_manager import ConfigManager

class GetTleSaocomSftp:
    """Clase que obtiene el TLE de los satelites SAOCOM en el MOC"""
    def __init__(self, tmp_dir, logger : logging.Logger):
        self.config_manager     = ConfigManager()
        self.config             = self.config_manager.config
        self.script_dir         = os.path.dirname(os.path.abspath(__file__))
        self.tmp_dir            = tmp_dir
        self.sftp_config        = self.config["sftp_moc_server"]
        self.satellite_config   = self.config["satellite_config"]
        self.sftp               = None
        self.client             = None
        self.logger             = logger
        self.connect_sftp()

    def connect_sftp(self):
        """Conexión SFTP con autoaceptación de claves del host"""
        try:
            if self.is_sftp_connected():
                self.logger.debug("Conexión SFTP ya activa, no se reconecta.")
                return

            # Cierra cualquier conexión anterior fallida o colgada
            self.close_sftp()

            # Inicio de nueva conexion
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Auto-confirmar claves nuevas
            client.connect(
                hostname=self.sftp_config["host"],
                #port=self.sftp_config["port"],
                username=self.sftp_config["user"],
                password=self.config_manager.read_secret(self.sftp_config["password"]),
                timeout=self.sftp_config["time_out"]
            )
            self.sftp = client.open_sftp()
            self.client = client
            self.logger.debug("Conexión SFTP establecida")
        except paramiko.SSHException as e:
            self.logger.error("Error al crear conexion SFTP: %s",e)
            self.logger.debug("Error al crear conexion SFTP -> conexión User/Passwd: %s:%s Host: %s",
                              self.sftp_config["user"],
                              self.config_manager.read_secret(self.sftp_config["password"]),
                              self.sftp_config["host"]
                              )

    def close_sftp(self):
        """Cierra la conexión SFTP y SSH si están abiertas"""
        try:
            if self.sftp:
                self.sftp.close()
                self.sftp = None
            if self.client:
                self.client.close()
                self.client = None
            self.logger.debug("Conexión SFTP cerrada correctamente")
        except Exception as e: # pylint: disable=broad-exception-caught
            self.logger.warning("Error al cerrar la conexión SFTP: %s", e)

    def is_sftp_connected(self):
        """Verifica si una conexion sigue activa o no"""
        try:
            if self.client and self.client.get_transport() and self.client.get_transport().is_active():
                self.sftp.listdir(".")  # Intenta listar algo para confirmar
                return True
        except Exception as e: # pylint: disable=broad-exception-caught
            self.logger.debug("Conexión SFTP no activa: %s", e)
        return False

    def traduce_name(self, tle: dict) -> dict:
        """
        Traduce el nombre del satelite a su nombre aceptado por las antenas
        Si se especifica un altername en la configuracion, se cambia el nombre del TLE
        """
        if self.satellite_config["satellite_altername"]:
            tle["line1"] = self.satellite_config["satellite_altername"]
            self.logger.debug("Se traduce el nombre del satelite a %s",self.satellite_config['satellite_altername'])
        return tle

    def check_processed(self,file_name : str) -> bool:
        """
        Verifica en la lista de procesadas el nombre del archivo, si no esta devuelve true
        """
        file_tle_bkp = os.path.join(self.tmp_dir, "procesadas.txt")
        if not os.path.exists(file_tle_bkp):
            with open(file_tle_bkp, "w", encoding='utf-8') as f:
                f.write("") # Creamos el archivo vacio
            self.logger.info("El archivo de backup no existe, se crea uno nuevo")
            list_processed = []
        else:
            with open(file_tle_bkp, "r", encoding='utf-8') as f:
                list_processed = [line.strip() for line in f.readlines()]
        self.logger.debug("lista processed: %s",list_processed)
        return file_name in list_processed

    def save_processed(self,file_name : str):
        """Guarda un nuevo nombre de archivo en la lista procesadas"""
        file_tle_bkp = os.path.join(self.tmp_dir, "procesadas.txt")
        list_processed = []
        if os.path.exists(file_tle_bkp):
            with open(file_tle_bkp, "r", encoding='utf-8') as f:
                list_processed = [line.strip() for line in f.readlines()]
            if file_name not in list_processed:
                list_processed.append(file_name)
            if len(list_processed) > 100: # cortamos la lista de procesados
                list_processed = list_processed[-50:]
            with open(file_tle_bkp, "w", encoding='utf-8') as f:
                for archive in list_processed:
                    f.write(f"{archive}\n")

    def get_tle(self,tle_type : str) -> dict | None:
        """Obtiene el ultimo TLE del satelite y devuelve un diccionario con el TLE"""
        try:
            if not tle_type:
                raise ValueError("El tipo de TLE no puede ser None")
            if self.sftp is None:
                raise ValueError("La conexion al SFTP no puede ser None")

            self.logger.debug("Directorio actual SFTP: %s", self.sftp.getcwd())
            self.sftp.chdir("/")        # Nos movemos al directorio raiz
            self.sftp.chdir(tle_type)   # Nos movemos al directorio PPM o TLE
            prefix = self.satellite_config["prefix"] + self.satellite_config["satellite"]
            files = [f for f in self.sftp.listdir_attr() if f.filename.startswith(prefix)]
            files.sort(key=lambda x: x.st_mtime, reverse=True)

            if files:
                lastfile = files[0].filename
                self.logger.debug("Ultimo archivo encontrado: %s", lastfile)
                if not self.check_processed(lastfile):
                    local_path = os.path.join(self.tmp_dir, lastfile)
                    with open(local_path, "wb") as f:
                        self.sftp.getfo(lastfile, f)

                    with gzip.open(local_path, "rt", encoding='utf-8') as  f:
                        lines = f.readlines()
                        if len(lines) >= 3:
                            tle_data = {
                                "satellite_name": lines[0].strip(),
                                "line1": lines[1].strip(),
                                "line2": lines[2].strip(),
                                "timestamp": files[0].st_mtime
                            }
                        else:
                            tle_data = None
                    self.logger.debug("TLE obtenido: %s", tle_data)
                    os.remove(local_path)
                    self.save_processed(lastfile)
                    return self.traduce_name(tle_data)
                self.logger.debug("El archivo ya fue procesado: %s", lastfile)
        except (paramiko.SSHException, paramiko.SFTPError) as e:
            self.logger.error(f"Error de conexión SFTP: {e}")
        except FileNotFoundError as e:
            self.logger.error(f"Error al abrir el archivo: {e}")
        except ValueError as e:
            self.logger.error(f"Error de valor: {e}")
        return None
