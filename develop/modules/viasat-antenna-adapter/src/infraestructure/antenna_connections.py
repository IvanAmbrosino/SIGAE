"""Modulo que se encarga de las conexiones para la carga de TLE en las antenas"""
import subprocess
import logging
from abc import ABC, abstractmethod
import paramiko
from sshtunnel import SSHTunnelForwarder, BaseSSHTunnelForwarderError


class Connection(ABC):
    """Clase abstracta para definir la estrategia de conexión (Aplicacion del Patrón Strategy)"""

    @abstractmethod
    def get_file(self, remote_path: str, local_path: str) -> bool:
        """Obtiene un archivo al servidor SFTP"""

    @abstractmethod
    def send_files(self, paths_to_file: list[str], destination_paths: list[str]) -> bool:
        """Envia un archivo al servidor SFTP"""

class SFTPDirect(Connection):
    """Clase que implementa la estrategia de conexión SFTP directa"""
    def __init__(self, host, username, password):
        self.host               = host
        self.username           = username
        self.password           = password
        self.ssh_client         = None
        self.sftp_client        = None
        self.logger = logging.getLogger("SFTPDirect")

    def connect(self):
        """Funcion que crea las conexiones ssh y sftp"""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.load_system_host_keys()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(self.host,
                                    username=self.username,
                                    password=self.password,
                                    timeout=10)
            self.sftp_client = self.ssh_client.open_sftp()
            return True
        except paramiko.ChannelException as e:
            self.logger.error("Error creando las conexiones SSH cliente %s",e)
        except paramiko.ssh_exception.SSHException as e:
            self.logger.error("Error en la conexion SSH: %s",e)
        return False

    def close_connections(self):
        """Cierra las conexiones SFTP y SSH"""
        if self.sftp_client:
            try:
                self.sftp_client.close()
                self.logger.debug("Cliente SFTP cerrado correctamente.")
            except Exception as e: # pylint: disable=broad-exception-caught
                self.logger.warning("No se pudo cerrar SFTP: %s", e)
        if self.ssh_client:
            try:
                self.ssh_client.close()
                self.logger.debug("Cliente SSH cerrado correctamente.")
            except Exception as e: # pylint: disable=broad-exception-caught
                self.logger.warning("No se pudo cerrar SFTP: %s", e)

    def get_file(self, remote_path: str, local_path: str) -> bool:
        """Obtiene un archivo al servidor SFTP"""
        sended = False
        self.connect()
        try:
            self.sftp_client.get(remote_path,local_path)
            sended = True

        except paramiko.ChannelException as e:
            self.logger.error("Error enviando el archivo al servidor destino: %s",e)
        except paramiko.ssh_exception.SSHException as e:
            self.logger.error("[GET ARCHIVE]Error en la conexion SSH: %s",e)
        finally:
            self.close_connections()
        return sended

    def send_files(self, paths_to_file: list[str], destination_paths: list[str]) -> bool:
        """Envía múltiples archivos al servidor SFTP a través de túneles SSH"""
        if len(paths_to_file) != len(destination_paths):
            self.logger.error("Cantidad de archivos locales y destinos no coinciden.")
            return False
        sended = False
        self.connect()
        try:
            for src, dst in zip(paths_to_file, destination_paths):
                self.sftp_client.put(src, dst)
            sended = True
        except Exception as e: # pylint: disable=broad-exception-caught
            self.logger.error("[SEND ARCHIVE] Error en la conexion SSH: %s",e)
        finally:
            self.close_connections()
        return sended

class SFTPTunnel(Connection):
    """Clase que implementa la estrategia de conexión SFTP a través de un túnel SSH"""
    def __init__(self, jump_host, jump_user, jump_password, target_host, target_user, target_password):
        self.jump_host          = jump_host
        self.jump_user          = jump_user
        self.jump_password      = jump_password
        self.target_host        = target_host
        self.target_user        = target_user
        self.target_password    = target_password
        self.sftp               = None
        self.transport          = None
        self.logger = logging.getLogger("SFTPTunnel")

    def close_connections(self):
        """Cierra las conexiones SFTP y SSH"""
        if self.sftp:
            try:
                self.sftp.close()
                self.logger.debug("SFTP cerrado correctamente.")
            except Exception as e: # pylint: disable=broad-exception-caught
                self.logger.warning("No se pudo cerrar SFTP: %s", e)
        if self.transport:
            try:
                self.transport.close()
                self.logger.debug("Transport cerrado correctamente.")
            except Exception as e: # pylint: disable=broad-exception-caught
                self.logger.warning("No se pudo cerrar Transport: %s", e)

    def send_files(self, paths_to_file: list[str], destination_paths: list[str]) -> bool:
        """Envia una lista de archivos al servidor SFTP"""
        sended = False
        try:
            with SSHTunnelForwarder(
                (self.jump_host, 22),                           # Dirección y puerto del servidor intermedio
                ssh_username        = self.jump_user,
                ssh_private_key     = None,
                ssh_password        = self.jump_password,
                remote_bind_address = (self.target_host, 22),   # Dirección y puerto de la VM
                local_bind_address  = ('127.0.0.1', 2222)       # Puerto local para el túnel
            ) as tunnel:
                self.transport = paramiko.Transport(('127.0.0.1', tunnel.local_bind_port))
                self.transport.connect(
                    username=self.target_user,
                    password=self.target_password
                )
                self.sftp = paramiko.SFTPClient.from_transport(self.transport)
                for src, dst in zip(paths_to_file, destination_paths):
                    self.sftp.put(src, dst)
                sended = True

        except paramiko.ChannelException as e:
            self.logger.error("[SEND FILE] Error enviando el archivo al servidor destino: %s",e)
        except paramiko.ssh_exception.SSHException as e:
            self.logger.error("[SEND FILE] Error en la conexion SSH: %s",e)
        except subprocess.CalledProcessError as e:
            self.logger.error("[SEND FILE] El TLE fue rechazado: %s",e)
        except BaseSSHTunnelForwarderError as e:
            self.logger.error("[SEND FILE] Failed to connect to server: %s. Retrying in 5 seconds...",e)
        finally:
            self.close_connections()
        return sended

    def get_file(self, remote_path: str, local_path: str) -> bool:
        """Obtiene un archivo al servidor SFTP"""
        sended = False
        try:
            with SSHTunnelForwarder(
                (self.jump_host, 22),                           # Dirección y puerto del servidor intermedio
                ssh_username        = self.jump_user,
                ssh_private_key     = None,
                ssh_password        = self.jump_password,
                remote_bind_address = (self.target_host, 22),   # Dirección y puerto de la VM
                local_bind_address  = ('127.0.0.1', 2222)       # Puerto local para el túnel
            ) as tunnel:
                self.transport = paramiko.Transport(('127.0.0.1', tunnel.local_bind_port))
                self.transport.connect(
                    username=self.target_user,
                    password=self.target_password
                )
                self.sftp = paramiko.SFTPClient.from_transport(self.transport)
                self.sftp.get(remote_path,local_path)
                sended = True

        except paramiko.ChannelException as e:
            self.logger.error("[GET FILE] Error enviando el archivo al servidor destino: %s",e)
        except paramiko.ssh_exception.SSHException as e:
            self.logger.error("[GET FILE] Error en la conexion SSH: %s",e)
        except subprocess.CalledProcessError as e:
            self.logger.error("[GET FILE] El TLE fue rechazado: %s",e)
        except BaseSSHTunnelForwarderError as e:
            self.logger.error("[GET FILE] Failed to connect to server: %s. Retrying in 5 seconds...",e)
        finally:
            self.close_connections()
        return sended

class SFTPDobleTunnel(Connection):
    """Clase que implementa la estrategia de conexión SSH a través de dos túneles"""
    def __init__(self, jump1_host, jump1_user, jump1_pass,
                 jump2_host, jump2_user, jump2_pass,
                 target_host, target_user, target_pass):
        self.jump1_host = jump1_host
        self.jump1_user = jump1_user
        self.jump1_pass = jump1_pass
        self.jump2_host = jump2_host
        self.jump2_user = jump2_user
        self.jump2_pass = jump2_pass
        self.target_host = target_host
        self.target_user = target_user
        self.target_pass = target_pass
        self.sftp               = None
        self.transport          = None
        self.logger = logging.getLogger("SFTPDoubleTunnel")


    def close_connections(self):
        """Cierra las conexiones SFTP y SSH"""
        if self.sftp:
            try:
                self.sftp.close()
                self.logger.debug("SFTP cerrado correctamente.")
            except Exception as e: # pylint: disable=broad-exception-caught
                self.logger.warning("No se pudo cerrar SFTP: %s", e)
        if self.transport:
            try:
                self.transport.close()
                self.logger.debug("Transport cerrado correctamente.")
            except Exception as e: # pylint: disable=broad-exception-caught
                self.logger.warning("No se pudo cerrar Transport: %s", e)

    def get_file(self, remote_path: str, local_path: str) -> bool:
        """Obtiene un archivo al servidor SFTP"""
        sended = False
        try:
            with SSHTunnelForwarder(
                (self.jump1_host, 22),
                ssh_username=self.jump1_user,
                ssh_private_key=None,
                ssh_password=self.jump1_pass,
                remote_bind_address=(self.jump2_host, 22),
            ) as tunnel1:
                self.logger.info("Primer túnel creado (hacia intermediario_1).")
                with SSHTunnelForwarder(
                    ("127.0.0.1", tunnel1.local_bind_port),
                    ssh_username=self.jump2_user,
                    ssh_private_key=None,
                    ssh_password=self.jump2_pass,
                    remote_bind_address=(self.target_host, 22),
                ) as tunnel2:
                    self.logger.info("Segundo túnel creado (hacia intermediario_2).")
                    self.transport = paramiko.Transport(("127.0.0.1", tunnel2.local_bind_port))
                    self.transport.connect(
                        username=self.target_user,
                        password=self.target_pass
                    )
                    self.sftp = paramiko.SFTPClient.from_transport(self.transport)
                    self.sftp.get(remote_path,local_path)
                    sended = True

        except paramiko.ChannelException as e:
            self.logger.error("[GET FILE] Error enviando el archivo al servidor destino: %s",e)
        except paramiko.ssh_exception.SSHException as e:
            self.logger.error("[GET FILE] Error en la conexion SSH: %s",e)
        except subprocess.CalledProcessError as e:
            self.logger.error("[GET FILE] El TLE fue rechazado: %s",e)
        except BaseSSHTunnelForwarderError as e:
            self.logger.error("[GET FILE] Failed to connect to server: %s. Retrying in 5 seconds...",e)
        finally:
            self.close_connections()
        return sended

    def send_files(self, paths_to_file: list[str], destination_paths: list[str]) -> bool:
        """Envia un archivo al servidor SFTP"""
        sended = False
        try:
            with SSHTunnelForwarder(
                (self.jump1_host, 22),
                ssh_username=self.jump1_user,
                ssh_private_key=None,
                ssh_password=self.jump1_pass,
                remote_bind_address=(self.jump2_host, 22),
            ) as tunnel1:
                self.logger.info("Primer túnel creado (hacia intermediario_1).")
                with SSHTunnelForwarder(
                    ("127.0.0.1", tunnel1.local_bind_port),
                    ssh_username=self.jump2_user,
                    ssh_private_key=None,
                    ssh_password=self.jump2_pass,
                    remote_bind_address=(self.target_host, 22),
                ) as tunnel2:
                    self.logger.info("Segundo túnel creado (hacia intermediario_2).")
                    self.transport = paramiko.Transport(("127.0.0.1", tunnel2.local_bind_port))
                    self.transport.connect(
                        username=self.target_user,
                        password=self.target_pass
                    )
                    self.sftp = paramiko.SFTPClient.from_transport(self.transport)
                    for src, dst in zip(paths_to_file, destination_paths):
                        self.sftp.put(src, dst)
                    sended = True

        except paramiko.ChannelException as e:
            self.logger.error("[SEND FILE] Error enviando el archivo al servidor destino: %s",e)
        except paramiko.ssh_exception.SSHException as e:
            self.logger.error("[SEND FILE] Error en la conexion SSH: %s",e)
        except subprocess.CalledProcessError as e:
            self.logger.error("[SEND FILE] El TLE fue rechazado: %s",e)
        except BaseSSHTunnelForwarderError as e:
            self.logger.error("[SEND FILE] Failed to connect to server: %s. Retrying in 5 seconds...",e)
        finally:
            self.close_connections()
        return sended
