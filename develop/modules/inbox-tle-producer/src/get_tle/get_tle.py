"""Busca el TLE de los satelites SAOCOM en el MOC"""
import logging
import paramiko
from datetime import datetime
from config_manager import ConfigManager

class GetTleInbox():
    """Clase que obtiene el TLE de los satelites SAOCOM en el MOC"""
    def __init__(self, tmp_dir, logger : logging.Logger):
        self.config_manager     = ConfigManager()
        self.sftp_config        = self.config_manager.config["sftp_server"]
        self.tmp_dir            = tmp_dir
        self.logger             = logger

        self.sftp               = None
        self.client             = None

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
        En este caso solo reemplaza los espacios por guiones bajos
        """
        tle["satellite_name"] = tle["satellite_name"].replace(" ", "_")
        return tle

    def get_tle(self) -> dict | None:
        """Obtiene el ultimo TLE del inbox y devuelve un diccionario"""
        try:
            if self.sftp is None:
                raise ValueError("La conexion al SFTP no puede ser None")

            self.sftp.chdir(self.sftp_config["directory"]) # Cambia al directorio inbox
            suffix = self.sftp_config["file_suffix"]
            prefix = self.sftp_config["file_prefix"]
            files = [f for f in self.sftp.listdir_attr() if f.filename.startswith(prefix) and f.filename.endswith(suffix)]
            files.sort(key=lambda x: x.st_mtime, reverse=True)

            if files:
                lastfile = files[0].filename
                self.logger.debug("Archivo encontrado: %s", lastfile)

                with self.sftp.open(lastfile, "r") as  f:
                    lines = f.readlines()
                    if len(lines) >= 3:
                        tle_data = {
                            "satellite_name": lines[0].strip(),
                            "line1": lines[1].strip(),
                            "line2": lines[2].strip(),
                            "timestamp": datetime.now()
                        }
                    else:
                        tle_data = None
                    self.logger.debug("TLE obtenido: %s", tle_data)
                    self.sftp.remove(lastfile)
                    return self.traduce_name(tle_data)
                self.logger.debug("El archivo ya fue procesado: %s", lastfile)
        except (paramiko.SSHException, paramiko.SFTPError) as e:
            self.logger.error(f"Error de conexión SFTP: {e}")
        except FileNotFoundError as e:
            self.logger.error(f"Error al abrir el archivo: {e}")
        except ValueError as e:
            self.logger.error(f"Error de valor: {e}")
        return None
