from get_tle_from_api import GestorTLE


if __name__ == "__main__":
    gestor = GestorTLE(kafka_topic="TLE")
    gestor.obtener_tles()