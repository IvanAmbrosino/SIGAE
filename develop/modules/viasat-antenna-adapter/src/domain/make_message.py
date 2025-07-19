"""Creacion de mensajes"""
from datetime import datetime, timezone

class MakeMessages():
    """Clase de armado de mensajes para enviar"""
    def __init__(self):
        pass

    def make_ack_message(self, planning_message):
        """
        Function that creates the ack message with the data from the original scheduling message
        """
        ack_message = {
            "message_type": "ACK",
            "norad_id": planning_message['norad_id'],
            "satellite_name": planning_message['satellite'],
            "task_id": planning_message['task_id'],
            "antenna_id": planning_message['antenna_id'],
            "timestamp": self.to_iso_z(datetime.utcnow())
        }
        return ack_message

    def to_iso_z(self, s: str) -> str:
        """Convierte fecha en texto o datetime a formato ISO con 'Z'"""
        if isinstance(s, str):
            s = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return s.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
