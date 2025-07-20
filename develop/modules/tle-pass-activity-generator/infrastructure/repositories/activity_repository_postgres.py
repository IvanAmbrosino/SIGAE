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

    def save_pass_activities(self, passes: List[PassActivity]) -> None:
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
            conn.commit()


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
    
    def assign_antenna_to_activity(self, activity_id: str, antenna_id: str, assigned_by: Optional[str]) -> None:
        assignment_id = str(uuid.uuid4())
        with get_db_connection(self.db_config) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO activity_assignments (id, activity_id, antenna_id, assigned_by)
                    VALUES (%s, %s, %s, %s)
                """, (assignment_id, activity_id, antenna_id, assigned_by))
            conn.commit()