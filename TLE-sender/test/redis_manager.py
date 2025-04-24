"""Modulo encargado de la conexion y obtencion de los tle de la base de datos Redis"""
import json
import redis
from config_manager import ConfigManager

class GetTleReddis():
    """Clase con la logica de obtencion del TLE de la base de datos Redis"""
    def __init__(self):
        """Carga la configuracion para conectarse a Redis"""
        # Configuración de conexión
        cm = ConfigManager()
        self.redis_host = cm.config["tle_request"]["redis_host"]
        self.redis_port = cm.config["tle_request"]["redis_port"]
        self.redis_password = cm.read_secret(cm.config["tle_request"]["secret_redis_path"])
        self.client = None

    def connect_reddis(self):
        """Funcion que abre una conexion a Redis"""
        try:
            self.client = redis.StrictRedis(host=self.redis_host, port=self.redis_port, password=self.redis_password, decode_responses=True)
            pong = self.client.ping() # Prueba de conexión
            if pong:
                print("Conexión exitosa a Redis")
        except redis.ConnectionError as e:
            print(f"Error al conectar con Redis: {e}")

    def disconect_redis(self):
        """Funcion que cierra la conexion de Redis"""
        try:
            pong = self.client.ping()
            if pong:
                self.client.close()
        except redis.ConnectionError as e:
            print(f"Error al conectar con Redis: {e}")

    def get_latest_tle(self,norad_id):
        """Obtiene el ultimo TLE para un satelite en particular"""
        try:
            self.connect_reddis()
            latest_tle = self.client.lindex(norad_id, 0)  # Se obtiene el ultimo elemento agregado
            self.disconect_redis()
            print(f"El ultimo TLE para el satelite {norad_id} es: {latest_tle}")
            return json.loads(latest_tle) if latest_tle else None
        except redis.ConnectionError as e:
            print(f"Error al conectar con Redis: {e}")
            return None
