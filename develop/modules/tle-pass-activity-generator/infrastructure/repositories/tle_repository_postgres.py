from domain.ports.tle_repository import TleRepository
from infrastructure.db import get_db_connection
from domain.entities.tle_data import TleData


class PostgresTleRepository(TleRepository):
    def __init__(self, db_config):
        self.db_config = db_config

    def save_tle_data(self, tle: TleData) -> None:
        with get_db_connection(self.db_config) as conn:
            with conn.cursor() as cur:
                query = """
                    INSERT INTO tle_data (id, satellite_id, line1, line2, epoch, source, is_valid, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING;
                """
                cur.execute(query, (
                    tle.id,
                    tle.satellite_id,
                    tle.line1,
                    tle.line2,
                    tle.epoch,
                    tle.source,
                    tle.is_valid,
                    tle.created_at,
                ))
                conn.commit()
