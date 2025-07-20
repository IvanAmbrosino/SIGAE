# domain/ports/pass_activity_repository.py
from abc import ABC, abstractmethod
from domain.entities.pass_activity import PassActivity
from typing import List, Optional
from datetime import datetime, timedelta, timezone

class ActivityRepository(ABC):
    
    @abstractmethod
    def save_pass_activities(self, passes: List[PassActivity]) -> None:
        pass

    @abstractmethod
    def is_antenna_available(self, antenna_id: str, start_time: datetime, end_time: datetime) -> bool:
        pass

    @abstractmethod
    def assign_antenna_to_activity(self, activity_id: str, antenna_id: str, assigned_by: Optional[str]) -> None:
        pass