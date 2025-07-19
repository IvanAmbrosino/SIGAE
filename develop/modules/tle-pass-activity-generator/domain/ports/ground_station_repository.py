from abc import ABC, abstractmethod
from typing import Optional, Dict

class GroundStationRepository(ABC):

    @abstractmethod
    def get_ground_station_config(self, station_name: str = "Estación Córdoba") -> Optional[Dict]:
        pass

    @abstractmethod
    def get_station_coordinates(self, station_name: str = "Estación Córdoba") -> Optional[tuple]:
        pass