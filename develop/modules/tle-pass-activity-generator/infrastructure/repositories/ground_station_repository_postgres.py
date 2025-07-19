from typing import Optional, Dict
from domain.ports.ground_station_repository import GroundStationRepository
from infrastructure.db import get_db_connection

class PostgresGroundStationRepository(GroundStationRepository):
    def __init__(self, db_config):
        self.db_config = db_config

    def get_ground_station_config(self, station_name: str = "Estación Córdoba") -> Optional[Dict]:
        with get_db_connection(self.db_config) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT gsc.default_propagation_hours, gsc.night_start_hour, gsc.night_end_hour
                    FROM ground_stations gs
                    JOIN ground_station_configurations gsc ON gs.id = gsc.ground_station_id
                    WHERE gs.name = %s AND gs.is_active = TRUE
                    LIMIT 1
                """, (station_name,))
                row = cur.fetchone()

        if row:
            return {
                'default_propagation_hours': row[0],
                'night_start_hour': row[1],
                'night_end_hour': row[2]
            }
        else:
            # Valores por defecto si no encuentra la config
            return {
                'default_propagation_hours': 24,
                'night_start_hour': 20,
                'night_end_hour': 6
            }

    def get_station_coordinates(self, station_name: str = "Estación Córdoba") -> Optional[tuple]:
        with get_db_connection(self.db_config) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT latitude, longitude, altitude
                    FROM ground_stations
                    WHERE name = %s AND is_active = TRUE
                    LIMIT 1
                """, (station_name,))
                row = cur.fetchone()

        if row:
            lat, lon, alt = float(row[0]), float(row[1]), float(row[2])
            return (lat, lon, alt)
        else:
            return None
