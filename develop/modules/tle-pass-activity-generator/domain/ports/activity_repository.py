# domain/ports/pass_activity_repository.py
from abc import ABC, abstractmethod
from domain.entities.pass_activity import PassActivity
from typing import List

class ActivityRepository(ABC):
    
    @abstractmethod
    def save_pass_activities(self, passes: List[PassActivity]) -> None:
        pass