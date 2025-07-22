"""Clases del dominio de la app SenderModule"""
from datetime import datetime

class Task():
    """Clase Task"""
    def __init__(self, task: dict):
        """Constructor de la clase Task"""
        self.task = {
            "task_id": task.get("task_id"),
            "satellite": task.get("satellite"),
            "action": task.get("action"),
            "antenna_id": task.get("antenna_id"),
            "norad_id": task.get("norad_id"),
            "config_id": task.get("config_id"),
            "start": task.get("start"),
            "end": task.get("end"),
            "prepass_seconds": task.get("prepass_seconds", 0),
            "postpass_seconds": task.get("postpass_seconds", 0)
        }

    def to_dict(self):
        """Convierte la task a un diccionario."""
        return self.task

class TLE():
    """Clase TLE"""
    def __init__(self, norad_id: str, satellite_name: str, tle_line1: str, tle_line2: str, timestamp: datetime):
        self.tle = {
            "norad_id": norad_id,
            "satellite_name": satellite_name,
            "tle_line1": tle_line1,
            "tle_line2": tle_line2,
            "timestamp": timestamp.isoformat()
        }

    def to_dict(self):
        """Convierte el TLE a un diccionario."""
        return self.tle
