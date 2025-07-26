# domain/ports/pass_activity_repository.py
from abc import ABC, abstractmethod
from domain.entities.pass_activity import PassActivity
from typing import List, Optional
from datetime import datetime, timedelta, timezone

class ActivityRepository(ABC):
    @abstractmethod
    def get_activity_by_id(self, activity_id: str) -> Optional[PassActivity]:
        """Devuelve la actividad (PassActivity) por su ID o None si no existe."""
        pass
    
    @abstractmethod
    def save_pass_activities(self, passes: List[PassActivity]) -> List[PassActivity]:
        """Guarda una lista de actividades (pasadas) y devuelve la lista con los IDs reales asignados."""
        pass

    @abstractmethod
    def is_antenna_available(self, antenna_id: str, start_time: datetime, end_time: datetime) -> bool:
        """Devuelve True si la antena está disponible en el rango horario indicado."""
        pass

    @abstractmethod
    def assign_antenna_to_activity(self, activity_id: str, antenna_id: str, configuration_id: str) -> None:
        """Asocia una antena y configuración a una actividad."""
        pass
    
    @abstractmethod
    def get_antenna_conflict(self, antenna_id: str, start_time, end_time) -> dict:
        """Devuelve la actividad en conflicto (si existe) y su prioridad para ese rango horario."""
        pass

    @abstractmethod
    def is_activity_registered(self, activity_id: str) -> bool:
        """Devuelve True si la actividad ya está registrada en la base de datos."""
        pass

    @abstractmethod
    def delete_activity(self, activity_id: str):
        """Elimina la actividad de la base de datos."""
        pass

    @abstractmethod
    def unassign_activity(self, activity_id: str):
        """Desasigna la antena de la actividad (sin eliminar la actividad)."""
        pass