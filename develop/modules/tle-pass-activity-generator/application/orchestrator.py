# application/orchestrator.py
from datetime import datetime, timedelta, timezone
import json
from typing import List

# Importacion de entidades
from domain.entities.pass_activity import PassActivity
from domain.entities.tle_data import TleData

# Importacion de services
from application.services.pass_activity_service import compute_passes
from application.services.tle_service import process_and_save_tle

# Importacion de interfaces 
from domain.ports.activity_repository import ActivityRepository
from domain.ports.ground_station_repository import GroundStationRepository
from domain.ports.satellite_repository import SatelliteRepository
from domain.ports.tle_repository import TleRepository

# importacion del logger
from infrastructure.logger import setup_logger

logger = setup_logger(__name__)


class Orchestrator:
    def __init__(
        self,
        tle_repository: TleRepository,
        satellite_repository: SatelliteRepository,
        ground_station_repository: GroundStationRepository,
        pass_activity_repository: ActivityRepository,
    ):
        self.tle_repository = tle_repository
        self.satellite_repository = satellite_repository
        self.ground_station_repository = ground_station_repository
        self.pass_activity_repository = pass_activity_repository

    def handle_tle_message(self, value: dict):
        logger.info(f"TLE recibido: {json.dumps(value, default=str)}")

        tle = process_and_save_tle(self.tle_repository, value)
        logger.info(f"TLE guardado: {json.dumps(tle.to_dict(), default=str)}")

        gs_config = self.ground_station_repository.get_ground_station_config()
        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(hours=gs_config['default_propagation_hours'])

        satellite = self.satellite_repository.get_satellite_by_id(tle.satellite_id)

        if not satellite:
            logger.warning(f"Satélite con ID {tle.satellite_id} no encontrado. Abortando cálculo de pasadas.")
            return

        if not satellite['can_propagate']:
            logger.info(f"Satélite {satellite['name']} no permite propagación, no se calculan pasadas.")
            return

        pasadas = compute_passes(tle, start_time, end_time, self.ground_station_repository, min_elevation=satellite['min_elevation'])

        valid_passes : List[PassActivity] = []
        for pasada in pasadas:
            elev = pasada.max_elevation  # valor de la elevación máxima de la pasada

            # Filtrar elevación máxima
            if satellite['max_elevation'] is not None and elev > satellite['max_elevation']:
                continue

            # descartar si no permite propagación en ese horario
            if not self._can_propagate_pass(pasada, satellite, gs_config):
                logger.info(f"Pasada descartada por restricción horario: {json.dumps(pasada.to_dict(), default=str)}")
                continue
            valid_passes.append(pasada)

        for pasada in valid_passes:
            logger.info(f"Pasada guardada: {json.dumps(pasada.to_dict(), default=str)}")

        self.pass_activity_repository.save_pass_activities(valid_passes)


    def _can_propagate_pass(self, pasada : PassActivity, satellite, gs_config) -> bool:
        hour = pasada.max_elevation_time.hour
        if self._is_nighttime(hour, gs_config['night_start_hour'], gs_config['night_end_hour']):
            return satellite['allow_nighttime_propagation']
        else:
            return satellite['allow_daytime_propagation']

    def _is_nighttime(self, hour: int, night_start: int, night_end: int) -> bool:
        if night_start < night_end:
            return night_start <= hour < night_end
        return hour >= night_start or hour < night_end
