# Aquí se define la entidad TLEPass y validaciones

from datetime import datetime
from enum import Enum

class Status(str, Enum):
    NEW = 'new'
    ASSIGNED = 'assigned'
    UNASSIGNED = 'unassigned'
    PENDING = 'pending'
    AUTHORIZED = 'authorized'
    PLANNED = 'planned'
    MODIFIED = 'modified'
    UPDATED = 'updated'
    CRITICAL = 'critical'

class Priority(str, Enum):
    CRITICAL = 'critical'
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'

class PassActivity:
    def __init__(
        self,
        satellite_id: str,
        start_time: datetime,
        max_elevation_time: datetime,
        end_time: datetime,
        duration: int,
        max_elevation: float,
        status: Status = Status.NEW,
        priority: Priority = Priority.MEDIUM,
        orbit_number: str | None = None,
    ):
        self.satellite_id = satellite_id
        self.start_time = start_time
        self.max_elevation_time = max_elevation_time
        self.end_time = end_time
        self.duration = duration
        self.max_elevation = max_elevation
        self.status = status
        self.priority = priority
        self.orbit_number = orbit_number

        self.validate()

    def validate(self):
        if self.start_time >= self.end_time:
            raise ValueError("start_time debe ser menor que end_time")
        if self.duration <= 0:
            raise ValueError("duration debe ser positivo")
        if not (0 <= self.max_elevation <= 180):
            raise ValueError("max_elevation debe estar entre 0 y 180 grados")

    def update_status(self, new_status: Status):
        self.status = new_status

    def update_priority(self, new_priority: Priority):
        self.priority = new_priority

    def to_dict(self):
        return {
            "satellite_id": self.satellite_id,
            "start_time": self.start_time,
            "max_elevation_time": self.max_elevation_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "max_elevation": self.max_elevation,
            "status": self.status.value,
            "priority": self.priority.value,
            "orbit_number": self.orbit_number,
        }


class TleData:
    def __init__(self, id: str, satellite_id: str, line1: str, line2: str, epoch: datetime, source: str, is_valid: bool = True, created_at: datetime = None):
        self.id = id
        self.satellite_id = satellite_id
        self.line1 = line1
        self.line2 = line2
        self.epoch = epoch
        self.source = source
        self.is_valid = is_valid
        self.created_at = created_at or datetime.utcnow()
    
    def to_dict(self):
        return {
            "id": self.id,
            "satellite_id": self.satellite_id,
            "line1": self.line1,
            "line2": self.line2,
            "epoch": self.epoch,
            "source": self.source,
            "is_valid": self.is_valid,
            "created_at": self.created_at,
        }