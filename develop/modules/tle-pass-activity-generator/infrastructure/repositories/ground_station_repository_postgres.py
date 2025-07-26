from typing import Optional, Dict, List
from domain.ports.ground_station_repository import GroundStationRepository
from infrastructure.db import get_db_connection
from domain.entities.antenna import Antenna, AntennaStatus


class PostgresGroundStationRepository(GroundStationRepository):

    def __init__(self, db_config):
        self.db_config = db_config

    def get_ground_station_config(self, station_name: str = "Estación Córdoba") -> Optional[Dict]:
        """Devuelve un dict con la configuración de la estación o None si no existe."""
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
        """Devuelve una tupla (lat, lon, alt) o None si no existe la estación."""
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
        
        
    def get_compatible_antennas(self, satellite_id: str) -> List[Antenna]:
        """Devuelve una lista de antenas compatibles con el satélite dado."""
        with get_db_connection(self.db_config) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT a.id, a.name, a.operational_status, a.is_active, a.model, a.quality_level
                    FROM antennas a
                    JOIN satellite_antenna_compatibility sac ON a.id = sac.antenna_id
                    WHERE sac.satellite_id = %s
                    AND a.operational_status = 'operational'
                    AND a.is_active = TRUE
                """, (satellite_id,))
                rows = cur.fetchall()

        return [
            Antenna(
                id=row[0], 
                name=row[1], 
                operational_status=AntennaStatus(row[2]), 
                is_active=row[3],
                model=row[4],
                quality_level=row[5]
            )
            for row in rows
        ]

    def get_activity_configuration_id(self, satellite_id: str, antenna_id: str) -> Optional[str]:
        """Devuelve el id de configuración activo para el par satélite-antena o None si no existe."""
        with get_db_connection(self.db_config) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT id FROM activity_configuration
                    WHERE satellite_id = %s AND antenna_id = %s AND is_active = TRUE
                    ORDER BY config_number ASC LIMIT 1
                ''', (satellite_id, antenna_id))
                row = cur.fetchone()
        if row:
            return row[0]
        return None