# domain/ports/tle_repository.py
from abc import ABC, abstractmethod
from domain.entities.tle_data import TleData

class TleRepository(ABC):

    @abstractmethod
    def save_tle_data(self, tle: TleData) -> None:
        pass