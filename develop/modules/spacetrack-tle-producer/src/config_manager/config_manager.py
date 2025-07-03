"""Modulo que obtiene las configuraciones"""
import os
from json import load

class ConfigManager():
    """Clase principal que obtiene las configuraciones"""
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_dir = self.script_dir + '/../configs'
        self.config_path = os.path.join(self.config_dir, 'config.json')
        self.config = self.load_config(self.config_path)

    def load_config(self, config_file):
        """Carga la configuracion desde el archivo de configuracion .json"""
        try:
            with open(config_file, "r", encoding='utf-8') as fp:
                data = load(fp)
                return data
        except (IOError,OSError) as err:
            print('Error reading configuration file -> %s. Error -> %s',config_file, err)
        return []

    def read_secret(self, secret):
        """Read secrets from docker and return it"""
        try:
            with open(f"{secret}", "r",encoding="utf-8") as sfile:
                return sfile.read().strip()
        except IOError as err:
            print("Error leyendo los secretos: %s ",err)
            return None

    def read_config_string(self, config_file):
        """Read a string from the config file"""
        try:
            with open(self.config_dir + "/" + config_file, "r", encoding='utf-8') as fp:
                return fp.read().strip()
        except (IOError,OSError) as err:
            print('Error reading configuration file -> %s. Error -> %s',config_file, err)
        return ""
