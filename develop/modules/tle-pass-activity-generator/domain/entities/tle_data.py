from datetime import datetime

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
