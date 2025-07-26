from typing import List, Optional
from domain.entities.pass_activity import PassActivity
from domain.ports.activity_repository import ActivityRepository
from infrastructure.db import get_db_connection
from psycopg2.extras import execute_values
import uuid
from datetime import datetime, timezone

class PostgresActivityRepository(ActivityRepository):
   
    def __init__(self, db_config):
        self.db_config = db_config

    def save_pass_activities(self, passes: List[PassActivity]) -> List[PassActivity]:
        # Filtrar duplicados por (satellite_id, orbit_number)
        seen = set()
        unique_pasadas : List[PassActivity] = []
        for pasada in passes:
            key = (pasada.satellite_id, pasada.orbit_number)
            if key not in seen:
                seen.add(key)
                unique_pasadas.append(pasada)

        sql = """
        INSERT INTO activities
        (id, satellite_id, orbit_number, start_time, max_elevation_time, max_elevation, end_time, duration, status, priority, created_at, updated_at)
        VALUES %s
        ON CONFLICT (satellite_id, orbit_number)
        DO UPDATE SET
            start_time = EXCLUDED.start_time,
            max_elevation_time = EXCLUDED.max_elevation_time,
            max_elevation = EXCLUDED.max_elevation,
            end_time = EXCLUDED.end_time,
            duration = EXCLUDED.duration,
            status = EXCLUDED.status,
            priority = EXCLUDED.priority,
            updated_at = EXCLUDED.updated_at
        """

        values = []
        for pasada in unique_pasadas:
            values.append((
                pasada.id,
                pasada.satellite_id,
                pasada.orbit_number,
                pasada.start_time,
                pasada.max_elevation_time,
                float(pasada.max_elevation),
                pasada.end_time,
                pasada.duration,
                pasada.status.value,
                pasada.priority.value,
                datetime.now(timezone.utc),
                datetime.now(timezone.utc)
            ))

        with get_db_connection(self.db_config) as conn:
            with conn.cursor() as cur:
                execute_values(cur, sql, values, template=None, page_size=100)
                # Para cada pasada, guardar el id original antes de sobrescribirlo
                result = []
                for pasada in unique_pasadas:
                    pasada._original_id = pasada.id  # Guardar el id generado en memoria
                    cur.execute(
                        "SELECT id FROM activities WHERE satellite_id = %s AND orbit_number = %s",
                        (pasada.satellite_id, pasada.orbit_number)
                    )
                    row = cur.fetchone()
                    if row:
                        pasada.id = row[0]
                    result.append(pasada)
            conn.commit()
        return result


    def is_antenna_available(self, antenna_id: str, start_time: datetime, end_time: datetime) -> bool:
        with get_db_connection(self.db_config) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 1
                    FROM activity_assignments aa
                    JOIN activities a ON aa.activity_id = a.id
                    WHERE aa.antenna_id = %s
                    AND tstzrange(a.start_time, a.end_time) && tstzrange(%s, %s)
                    LIMIT 1
                """, (antenna_id, start_time, end_time))
                conflict = cur.fetchone()
        return conflict is None
    
    def assign_antenna_to_activity(self, activity_id: str, antenna_id: str, configuration_id: str) -> None:
        assignment_id = str(uuid.uuid4())
        # ON CONFLICT (activity_id) DO UPDATE SET antenna_id = EXCLUDED.antenna_id, configuration_id = EXCLUDED.configuration_id, is_active = TRUE

        with get_db_connection(self.db_config) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO activity_assignments (id, activity_id, antenna_id, configuration_id, is_active)
                    VALUES (%s, %s, %s, %s, TRUE)
                """, (assignment_id, activity_id, antenna_id, configuration_id))
            conn.commit()

    def get_activity_by_id(self, activity_id: str) -> Optional[PassActivity]:
        with get_db_connection(self.db_config) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, satellite_id, start_time, max_elevation_time, end_time, duration, max_elevation, status, priority, orbit_number
                    FROM activities
                    WHERE id = %s
                """, (activity_id,))
                row = cur.fetchone()
                if not row:
                    return None
                return PassActivity(
                    id=row[0],
                    satellite_id=row[1],
                    start_time=row[2],
                    max_elevation_time=row[3],
                    end_time=row[4],
                    duration=row[5],
                    max_elevation=row[6],
                    status=row[7],
                    priority=row[8],
                    orbit_number=row[9]
                )

    def get_antenna_conflict(self, antenna_id: str, start_time, end_time) -> dict:
        """Devuelve la actividad en conflicto (si existe) y su prioridad para ese rango horario."""
        with get_db_connection(self.db_config) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT a.id, a.priority
                    FROM activity_assignments aa
                    JOIN activities a ON aa.activity_id = a.id
                    WHERE aa.antenna_id = %s
                    AND tstzrange(a.start_time, a.end_time) && tstzrange(%s, %s)
                    AND aa.is_active = TRUE
                    LIMIT 1
                ''', (antenna_id, start_time, end_time))
                row = cur.fetchone()
        if row:
            return {'activity_id': row[0], 'priority': row[1]}
        return None

    def is_activity_registered(self, activity_id: str) -> bool:
        with get_db_connection(self.db_config) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT 1 FROM activities WHERE id = %s LIMIT 1
                ''', (activity_id,))
                return cur.fetchone() is not None

    def delete_activity(self, activity_id: str):
        with get_db_connection(self.db_config) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    DELETE FROM activities WHERE id = %s
                ''', (activity_id,))
            conn.commit()

    def unassign_activity(self, activity_id: str):
        with get_db_connection(self.db_config) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    UPDATE activity_assignments SET is_active = FALSE, unassigned_at = CURRENT_TIMESTAMP
                    WHERE activity_id = %s AND is_active = TRUE
                ''', (activity_id,))
            conn.commit()