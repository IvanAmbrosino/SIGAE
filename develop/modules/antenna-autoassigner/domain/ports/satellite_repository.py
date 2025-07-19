from abc import ABC, abstractmethod
from typing import Optional, Dict

class SatelliteRepository(ABC):

    @abstractmethod
    def get_satellite_by_id(self, satellite_id: str) -> Optional[Dict]:
        """Devuelve un dict con datos o None si no existe"""
        pass
