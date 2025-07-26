from abc import ABC, abstractmethod
from typing import Optional, Dict, List
from domain.entities.antenna import Antenna

class GroundStationRepository(ABC):

    @abstractmethod
    def get_ground_station_config(self, station_name: str = "Estación Córdoba") -> Optional[Dict]:
        """Devuelve un dict con la configuración de la estación o None si no existe."""
        pass

    @abstractmethod
    def get_station_coordinates(self, station_name: str = "Estación Córdoba") -> Optional[tuple]:
        """Devuelve una tupla (lat, lon, alt) o None si no existe la estación."""
        pass

    @abstractmethod
    def get_compatible_antennas(self, satellite_id: str) -> List[Antenna]:
        """Devuelve una lista de antenas compatibles con el satélite dado."""
        pass

    @abstractmethod
    def get_activity_configuration_id(self, satellite_id: str, antenna_id: str) -> Optional[str]:
        """Devuelve el id de configuración activo para el par satélite-antena o None si no existe."""
        pass