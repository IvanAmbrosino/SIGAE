from enum import Enum
from typing import Optional

class AntennaStatus(str, Enum):
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    OUT_OF_SERVICE = "out_of_service"


class Antenna:
    def __init__(
        self, 
        id: str, 
        name: str, 
        operational_status: AntennaStatus, 
        is_active: bool, 
        model: Optional[str] = None,
        quality_level: Optional[str] = None,
    ):
        self.id = id
        self.name = name
        self.operational_status = operational_status
        self.is_active = is_active
        self.model = model
        self.quality_level = quality_level

    def is_operational(self):
        return self.operational_status == AntennaStatus.OPERATIONAL

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "operational_status": self.operational_status.value,
            "is_active": self.is_active,
            "model": self.model,
            "quality_level": self.quality_level,
        }
