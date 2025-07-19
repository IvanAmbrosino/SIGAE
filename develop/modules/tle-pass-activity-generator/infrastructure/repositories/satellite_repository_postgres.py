from typing import Optional, Dict
from domain.ports.satellite_repository import SatelliteRepository
from infrastructure.db import get_db_connection


class PostgresSatelliteRepository(SatelliteRepository):
    def __init__(self, db_config):
        self.db_config = db_config

    def get_satellite_by_id(self, satellite_id: str) -> Optional[Dict]:
        with get_db_connection(self.db_config) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, priority_level, description,
                        is_active, can_propagate, allow_daytime_propagation, allow_nighttime_propagation,
                        min_elevation, max_elevation
                    FROM satellites
                    WHERE id = %s
                    LIMIT 1
                """, (satellite_id,))
                row = cur.fetchone()

        if not row:
            return None

        return {
            'id': row[0],
            'name': row[1],
            'priority_level': row[2],
            'description': row[3],
            'is_active': row[4],
            'can_propagate': row[5],
            'allow_daytime_propagation': row[6],
            'allow_nighttime_propagation': row[7],
            'min_elevation': float(row[8]) if row[8] is not None else None,
            'max_elevation': float(row[9]) if row[9] is not None else None,
        }
