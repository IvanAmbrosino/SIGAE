from datetime import datetime, timedelta, timezone
from application.pass_activity_service import compute_passes
from application.tle_service import process_and_save_tle
from infrastructure.db import save_pass_activities, get_ground_station_config, get_satellite_by_id
import json
from infrastructure.logger import setup_logger

logger = setup_logger(__name__)



def handle_tle_message(conn, value: dict):
    
    logger.info(f"TLE recibido: {json.dumps(value, default=str)}")

    tle = process_and_save_tle(conn, value)
    
    logger.info(f"TLE guardado: {json.dumps(tle.to_dict(), default=str)}")


    # Obtener configuración estación
    gs_config = get_ground_station_config(conn)
    start_time = datetime.now(timezone.utc)
    end_time = start_time + timedelta(hours=gs_config['default_propagation_hours'])

    # Obtener datos satélite
    satellite = get_satellite_by_id(conn, tle.satellite_id)

    if not satellite:
        logger.warning(f"Satélite con ID {tle.satellite_id} no encontrado. Abortando cálculo de pasadas.")
        return

    if not satellite['can_propagate']:
        logger.info(f"Satélite {satellite['name']} no permite propagación, no se calculan pasadas.")
        return
    
    # Pasar el min_elevation para filtrar en el cálculo
    pasadas = compute_passes(conn, tle, start_time, end_time, min_elevation=satellite['min_elevation'])

    valid_passes = []
    for pasada in pasadas:
        elev = pasada.max_elevation  # valor de la elevación máxima de la pasada

        # Filtrar elevación máxima
        if satellite['max_elevation'] is not None and elev > satellite['max_elevation']:
            continue

        # descartar si no permite propagación en ese horario
        if not can_propagate_pass(pasada, satellite, gs_config):
            logger.info(f"Pasada descartada por restricción horario: {json.dumps(pasada.to_dict(), default=str)}")
            continue
        valid_passes.append(pasada)

    save_pass_activities(conn, valid_passes)


    for pasada in valid_passes:
        logger.info(f"Pasada guardada: {json.dumps(pasada.to_dict(), default=str)}")



# Decide si la pasada puede propagarse seg. día/noche y permisos del satélite
def can_propagate_pass(pasada, satellite: dict, gs_config: dict) -> bool:
    # obtener hora local UTC de la máxima elevación
    hour = pasada.max_elevation_time.hour
    if is_nighttime(hour, gs_config['night_start_hour'], gs_config['night_end_hour']):
        return satellite['allow_nighttime_propagation']
    else:
        return satellite['allow_daytime_propagation']
    
# Determina si una hora (0–23) está en período nocturno
def is_nighttime(hour: int, night_start: int, night_end: int) -> bool:
    if night_start < night_end:
        return night_start <= hour < night_end
    # cruza medianoche, ej. 20 → 6
    return hour >= night_start or hour < night_end