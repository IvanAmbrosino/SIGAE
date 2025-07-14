#ejecucion local
# from .get_tle_from_api import GestorTLE
from BL.get_tle_from_api import GestorTLE

if __name__ == "__main__":
    gestor = GestorTLE()
    gestor.obtener_tles()