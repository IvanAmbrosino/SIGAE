from datetime import datetime, timedelta, timezone
from application.pass_activity_service import compute_passes
from application.tle_service import process_and_save_tle
from infrastructure.db import save_pass_activities
import json
from infrastructure.logger import setup_logger

logger = setup_logger(__name__)



def handle_tle_message(conn, value: dict):
    
    logger.info(f"TLE recibido: {json.dumps(value, default=str)}")

    tle = process_and_save_tle(conn, value)
    logger.info(f"TLE guardado: {json.dumps(tle.to_dict(), default=str)}")

    start_time = datetime.now(timezone.utc)
    end_time = start_time + timedelta(hours=24)

    pasadas = compute_passes(tle, start_time, end_time)

    save_pass_activities(conn, pasadas)

    for pasada in pasadas:
        logger.info(f"Pasada guardada: {json.dumps(pasada.to_dict(), default=str)}")
