"""Modulo que se encarga de las conexiones para la carga de TLE en las antenas"""
import subprocess
from datetime import date
from time import sleep
import paramiko
from sshtunnel import SSHTunnelForwarder, BaseSSHTunnelForwarderError
from config_manager import ConfigManager


class Connections():
    """Carga el TLE en la antena. La funcion varía dependiendo de la antena destino."""
    def __init__(self,logger,base_dir):
        """Cargamos las configuraciones iniciales para la conexion con la antena"""
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        self.logger = logger
        self.await_time = 30                                        # Tiempo de espera a la confirmacion del archivo
        self.max_retrys = 5                                         # Reintentos maximos antes de que corte
        self.local_tmp = f"{base_dir}/tmp"                          # Directorio temporal
        self.tmp_archive = "/tle_tmp.txt"                           # Archivo temporal con el TLE a actualizar
        #self.tle_filename = f"/rciEphem_post_tle{date.today()}.txt" # Nombre del archivo a enviar
        self.tle_filename = f"/test_post_tle{date.today()}.txt"     # Nombre del archivo test a enviar

    def send_archive(self):
        """Logica de envio a las antenas"""
        delivered, retrys = False , 0
        while not delivered:
            if "datron" in self.config["type"]:
                delivered = self.post_tle_direct_datron()
            elif "viasat direct" in self.config["type"]:
                delivered = self.post_tle_direct_viasat()
            elif "viasat tunnel" in self.config["type"]:
                delivered = self.post_tle_tunnel_viasat()
            elif "viasat double tunnel" in self.config["type"]:
                delivered = self.post_tle_double_tunnel_viasat()
            if retrys >= self.max_retrys and delivered is False:
                self.logger.error("Limite de maximos reintentos")
                raise TimeoutError
            retrys += 1

    def create_ssh_client(self, server, user, password):
        """Funcion que crea la conexion ssh"""
        try:
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(server, username=user, password=password, timeout=10)
            return client
        except paramiko.ChannelException as e:
            self.logger.error("Error creando las conexiones SSH cliente %s",e)
        except paramiko.ssh_exception.SSHException as e:
            self.logger.error("Error en la conexion SSH: %s",e)
        return None

    def post_tle_direct_datron(self) -> bool:
        """Carga el TLE en la antena Datron. No verifica si el TLE fue aceptado."""
        destination_path = self.config_manager.config["server_config"]["destination_path"]
        ssh_client,delivered = None,False
        try:
            ssh_client = self.create_ssh_client(
                self.config["server_config"]["server_ip"],
                user=self.config["server_config"]["server_user"],
                password=self.config_manager.read_secret(self.config["server_config"]["server_password"])
                )
            sftp_client = ssh_client.open_sftp()
            sftp_client.put(f"{self.local_tmp}{self.tmp_archive}", f"{destination_path}tle_ETC.txt")
            sftp_client.close()
            ssh_client.close()
            delivered = True
        except paramiko.ChannelException as e:
            self.logger.error("Error enviando el archivo al servidor destino: %s",e)
        except paramiko.ssh_exception.SSHException as e:
            self.logger.error("Error en la conexion SSH: %s",e)
        return delivered

    def post_tle_direct_viasat(self) -> bool:
        """Carga el TLE pasado por parametro en la antena Viasat."""
        destination_path = self.config["server_config"]["destination_path"]
        ssh_client,delivered = None, False
        try:
            ssh_client = self.create_ssh_client(
                self.config["server_config"]["server_ip"],
                user=self.config["server_config"]["server_user"],
                password=self.config_manager.read_secret(self.config["server_config"]["server_password"])
                )
            sftp_client = ssh_client.open_sftp()
            sftp_client.put(f"{self.local_tmp}{self.tmp_archive}", f"{destination_path}{self.tle_filename}")
            sleep(self.await_time)
            remote_file_path = f"{destination_path}{self.tle_filename}"
            _, stdout, _ = ssh_client.exec_command(f"grep 'ACCEPTED' {remote_file_path}")
            result = stdout.read().decode().strip()

            if "ACCEPTED" in result:
                self.logger.info("El nuevo TLE fue Aceptado en la antena. Result: %s",result)
                delivered = True
            else:
                self.logger.error("La palabra 'ACCEPTED' no fue encontrada en el archivo. %s%s",destination_path,self.tle_filename)

        except paramiko.ChannelException as e:
            self.logger.error("Error enviando el archivo al servidor destino: %s",e)
        except paramiko.ssh_exception.SSHException as e:
            self.logger.error("Error en la conexion SSH: %s",e)
        sftp_client.close()
        ssh_client.close()
        return delivered

    def post_tle_tunnel_viasat(self) -> bool:
        """Carga el TLE pasado por parametro en la antena Viasat de 6.1 las cuales funcionan con SCC virtuales y hay q realizar un solo puente."""
        destination_dir = self.config["server_config"]["destination_path"]
        delivered = False
        try:
            with SSHTunnelForwarder(
                (self.config["server_tunnel"]["server_ip"], 22),  # Dirección y puerto del servidor intermedio
                ssh_username=self.config["server_tunnel"]["server_user"],
                ssh_private_key=None,
                ssh_password=self.config_manager.read_secret(self.config["server_tunnel"]["server_password"]),
                remote_bind_address=(self.config["server_config"]["server_ip"], 22),  # Dirección y puerto de la VM
                local_bind_address=('127.0.0.1', 2222)  # Puerto local para el túnel
            ) as tunnel:
                self.logger.info("Túnel SSH creado. Conectando a la máquina virtual...") # Configurar cliente SFTP
                transport = paramiko.Transport(('127.0.0.1', tunnel.local_bind_port))
                transport.connect(
                    username=self.config["server_config"]["server_user"],
                    password=self.config_manager.read_secret(self.config["server_config"]["server_password"])
                )
                sftp = paramiko.SFTPClient.from_transport(transport)
                sftp.put(f"{self.local_tmp}{self.tmp_archive}",f"{destination_dir}{self.tle_filename}") # Subir el archivo
                sleep(self.await_time)
                sftp.get(f"{destination_dir}{self.tle_filename}",f"{self.local_tmp}/verify.txt") # Descargar el archivo para verificar
                result = subprocess.run(["grep","ACCEPTED",f"{self.local_tmp}/verify.txt"],
                                        check=True, stdout=subprocess.PIPE).stdout.decode().strip()

                if "ACCEPTED" in result:
                    self.logger.info("El TLE fue cargado correctamente en el destino.")
                    delivered = True
                else:
                    self.logger.info("El TLE no fue aceptado.")

        except paramiko.ChannelException as e:
            self.logger.error("Error enviando el archivo al servidor destino: %s",e)
        except paramiko.ssh_exception.SSHException as e:
            self.logger.error("Error en la conexion SSH: %s",e)
        except subprocess.CalledProcessError as e:
            self.logger.error("El TLE fue rechazado: %s",e)
        except BaseSSHTunnelForwarderError as e:
            self.logger.error("Failed to connect to server: %s. Retrying in 5 seconds...",e)
        sftp.close()
        transport.close()
        return delivered

    def post_tle_double_tunnel_viasat(self):
        """Carga el TLE pasado por parametro en la antena Viasat de 6.1 y 5.4 las cuales funcionan con SCC virtuales y hay q realizar un puente."""
        destination_dir = self.config["server_config"]["destination_path"]
        delivered = False
        try:
            with SSHTunnelForwarder(
                (self.config["server_tunnel"]["server_ip"], 22),
                ssh_username=self.config["server_tunnel"]["server_user"],
                ssh_private_key=None,
                ssh_password=self.config_manager.read_secret(self.config["server_tunnel"]["server_password"]),
                remote_bind_address=(self.config["second_server_tunnel"]["server_ip"], 22),
            ) as tunnel1:
                self.logger.info("Primer túnel creado (hacia intermediario_1).")

                with SSHTunnelForwarder(
                    ("127.0.0.1", tunnel1.local_bind_port),
                    ssh_username=self.config["second_server_tunnel"]["server_user"],
                    ssh_private_key=None,
                    ssh_password=self.config_manager.read_secret(self.config["second_server_tunnel"]["server_password"]),
                    remote_bind_address=(self.config["server_config"]["server_ip"], 22),
                ) as tunnel2:
                    self.logger.info("Segundo túnel creado (hacia intermediario_2).")

                    # Conexión SFTP a través del segundo túnel
                    transport = paramiko.Transport(("127.0.0.1", tunnel2.local_bind_port))
                    transport.connect(
                        username=self.config["server_config"]["server_user"],
                        password=self.config_manager.read_secret(self.config["server_config"]["server_password"])
                    )
                    sftp = paramiko.SFTPClient.from_transport(transport)
                    sftp.put(f"{self.local_tmp}{self.tmp_archive}",f"{destination_dir}{self.tle_filename}")
                    sleep(self.await_time)
                    sftp.get(f"{destination_dir}{self.tle_filename}",f"{self.local_tmp}/verify.txt")
                    result = subprocess.run(["grep","ACCEPTED",f"{self.local_tmp}/verify.txt"],
                                            check=True, stdout=subprocess.PIPE).stdout.decode().strip()
                    if "ACCEPTED" in result:
                        self.logger.info("El TLE fue cargado correctamente en el destino.")
                        delivered = True
                    else:
                        self.logger.info("El TLE no fue aceptado.")

        except paramiko.ChannelException as e:
            self.logger.error("Error enviando el archivo al servidor destino: %s",e)
        except paramiko.ssh_exception.SSHException as e:
            self.logger.error("Error en la conexion SSH: %s",e)
        except subprocess.CalledProcessError as e:
            self.logger.error("El TLE fue rechazado: %s",e)
        except BaseSSHTunnelForwarderError as e:
            self.logger.error("Failed to connect to server: %s. Retrying in 5 seconds...",e)
        sftp.close()
        transport.close()
        return delivered
