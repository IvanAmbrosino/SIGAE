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
        status: Status = Status.NEW,
        priority: Priority = Priority.MEDIUM,
        orbit_number: str | None = None,
    ):
        self.satellite_id = satellite_id
        self.start_time = start_time
        self.max_elevation_time = max_elevation_time
        self.end_time = end_time
        self.duration = duration
        self.status = status
        self.priority = priority
        self.orbit_number = orbit_number

        self.validate()

    def validate(self):
        if self.start_time >= self.end_time:
            raise ValueError("start_time debe ser menor que end_time")
        if self.duration <= 0:
            raise ValueError("duration debe ser positivo")
        # más validaciones según reglas del dominio

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
            "status": self.status.value,
            "priority": self.priority.value,
            "orbit_number": self.orbit_number,
        }
