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
        """Procesa un mensaje TLE recibido, calcula pasadas, guarda actividades y asigna antenas automáticamente."""
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

        # Guardar actividades y obtener los ids reales (insertados o actualizados)
        valid_passes_db = self.pass_activity_repository.save_pass_activities(valid_passes)

        # Log personalizado: distinguir entre insertada y actualizada
        for pasada, pasada_db in zip(valid_passes, valid_passes_db):
            original_id = getattr(pasada, '_original_id', pasada.id)
            if original_id == pasada_db.id:
                logger.info(f"Pasada guardada: {json.dumps(pasada_db.to_dict(), default=str)}")
            else:
                logger.info(f"Pasada actualizada por repetición de (satellite_id, orbit_number): {json.dumps(pasada_db.to_dict(), default=str)}")
                
        # Asignar antena automáticamente a cada actividad
        self.assign_antennas_to_activities(valid_passes_db)

    
    
    PRIORITY_ORDER = {
        'critical': 4,
        'high': 3,
        'medium': 2,
        'low': 1
    }

    def assign_antennas_to_activities(self, activities: List[PassActivity]):
        """Asigna antenas a una lista de actividades considerando compatibilidad y prioridades."""
        for activity in activities:
            compatible_antennas = self.ground_station_repository.get_compatible_antennas(activity.satellite_id)
            assigned = False
            for antenna in compatible_antennas:
                # Obtener id de configuración para el par satélite-antena
                config_id = self.ground_station_repository.get_activity_configuration_id(activity.satellite_id, antenna.id)
                # Verifica disponibilidad y obtiene conflicto si existe
                conflict = self.pass_activity_repository.get_antenna_conflict(
                    antenna_id=antenna.id,
                    start_time=activity.start_time,
                    end_time=activity.end_time
                )
                if not conflict:
                    # Asignar normalmente
                    self.pass_activity_repository.assign_antenna_to_activity(
                        activity_id=activity.id,
                        antenna_id=antenna.id,
                        configuration_id=config_id
                    )
                    logger.info(
                        f"Antenna {antenna.name} asignada a actividad {activity.id} "
                        f"desde {activity.start_time.isoformat()} hasta {activity.end_time.isoformat()} (config: {config_id})"
                    )
                    assigned = True
                    break
                else:
                    # Hay conflicto, comparar prioridades usando PRIORITY_ORDER
                    conflict_priority = conflict['priority']
                    new_priority = activity.priority
                    conflict_priority_value = self.PRIORITY_ORDER.get(conflict_priority, 0)
                    new_priority_value = self.PRIORITY_ORDER.get(new_priority, 0)

                    if new_priority_value > conflict_priority_value:
                        # Reemplazar: desasignar la actividad en conflicto y asignar la nueva
                        self.pass_activity_repository.unassign_activity(conflict['activity_id'])
                        logger.info(f"Actividad {conflict['activity_id']} desasignada por prioridad inferior a {activity.id}")
                        self.pass_activity_repository.assign_antenna_to_activity(
                            activity_id=activity.id,
                            antenna_id=antenna.id,
                            configuration_id=config_id
                        )
                        logger.info(
                            f"Antenna {antenna.name} asignada a actividad {activity.id} (reemplazó a {conflict['activity_id']}) "
                            f"desde {activity.start_time.isoformat()} hasta {activity.end_time.isoformat()} (config: {config_id})"
                        )
                        # Intentar reubicar la actividad desplazada
                        self._try_reassign_activity(conflict['activity_id'], conflict_priority)
                        assigned = True
                        break

                    elif new_priority_value == conflict_priority_value:
                        logger.warning(
                            f"No se asigna actividad {activity.id} a {antenna.name} por prioridad igual a la existente ({conflict['activity_id']})"
                        )
                        continue
                    else:
                        # Prioridad menor, buscar otra antena
                        continue
                    
            if not assigned:
                # Si la actividad ya estaba registrada y no se pudo reubicar, eliminarla
                if self.pass_activity_repository.is_activity_registered(activity.id):
                    self.pass_activity_repository.delete_activity(activity.id)
                    logger.warning(
                        f"Actividad {activity.id} eliminada: no se encontró antena disponible para reubicar (rango: {activity.start_time.isoformat()} → {activity.end_time.isoformat()})"
                    )
                else:
                    logger.warning(
                        f"No se encontró antena disponible para la actividad {activity.id} "
                        f"(rango: {activity.start_time.isoformat()} → {activity.end_time.isoformat()})"
                    )

    def _try_reassign_activity(self, activity_id, priority):
        """Intenta reubicar una actividad desplazada por prioridad."""
        
        logger.info(f"Intentando reubicar actividad desplazada {activity_id} (prioridad {priority})")
        # Obtener la actividad de la base de datos
        activity = self.pass_activity_repository.get_activity_by_id(activity_id)
        if not activity:
            logger.warning(f"No se pudo reubicar la actividad {activity_id} porque no existe en la base de datos.")
            return
        
        compatible_antennas = self.ground_station_repository.get_compatible_antennas(activity.satellite_id)

        priority_value = self.PRIORITY_ORDER.get(priority, 0)

        for antenna in compatible_antennas:
            config_id = self.ground_station_repository.get_activity_configuration_id(activity.satellite_id, antenna.id)
            conflict = self.pass_activity_repository.get_antenna_conflict(
                antenna_id=antenna.id,
                start_time=activity.start_time,
                end_time=activity.end_time
            )
            if not conflict:
                self.pass_activity_repository.assign_antenna_to_activity(
                    activity_id=activity.id,
                    antenna_id=antenna.id,
                    configuration_id=config_id
                )
                logger.info(
                    f"Actividad {activity.id} reubicada en antena {antenna.name} (config: {config_id}) "
                    f"desde {activity.start_time.isoformat()} hasta {activity.end_time.isoformat()}"
                )
                return
            else:
                conflict_priority = conflict['priority']
                conflict_priority_value = self.PRIORITY_ORDER.get(conflict_priority, 0)
                if priority_value > conflict_priority_value:
                    self.pass_activity_repository.unassign_activity(conflict['activity_id'])
                    logger.info(f"Actividad {conflict['activity_id']} desasignada por prioridad inferior a {activity.id} (reubicación)")
                    self.pass_activity_repository.assign_antenna_to_activity(
                        activity_id=activity.id,
                        antenna_id=antenna.id,
                        configuration_id=config_id
                    )
                    logger.info(
                        f"Actividad {activity.id} reubicada en antena {antenna.name} reemplazando a {conflict['activity_id']} (config: {config_id})"
                    )
                    self._try_reassign_activity(conflict['activity_id'], conflict['priority'])
                    return
        # Si no se pudo reubicar
        self.pass_activity_repository.delete_activity(activity.id)
        logger.warning(f"Actividad {activity.id} eliminada: no se pudo reubicar tras ser desplazada por prioridad.")


    def _can_propagate_pass(self, pasada : PassActivity, satellite, gs_config) -> bool:
        """Devuelve True si la pasada puede propagarse según la configuración horaria y el satélite."""
        hour = pasada.max_elevation_time.hour
        if self._is_nighttime(hour, gs_config['night_start_hour'], gs_config['night_end_hour']):
            return satellite['allow_nighttime_propagation']
        else:
            return satellite['allow_daytime_propagation']

    def _is_nighttime(self, hour: int, night_start: int, night_end: int) -> bool:
        """Devuelve True si la hora indicada corresponde al horario nocturno configurado."""
        if night_start < night_end:
            return night_start <= hour < night_end
        return hour >= night_start or hour < night_end

