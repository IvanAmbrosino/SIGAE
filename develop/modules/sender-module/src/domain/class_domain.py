"""Clases del dominio de la app SenderModule"""
from datetime import datetime

class Activities():
    """Class that creates an Activity instance with all its assignments and data"""
    def __init__(self, activities: dict):
        """
        Constructor of the Activities class
        
        Create a dictionary with the following, indexed by activity ID:

            - "datos": dict -> The activity data
            - "asignaciones": list[dict] -> Each of the assignments related to that activity
        """
        self.activities = {}
        if activities:
            for activity in activities:
                if activity['activity_id'] not in self.activities:
                    self.activities[activity['activity_id']] = {
                        'datos': {
                            'id': activity['activity_id'],
                            'satellite_id': activity['satellite_id'],
                            'satellite_name': activity['satellite_name'],
                            'orbit_number': activity['orbit_number'],
                            'start_time': activity['start_time'],
                            'max_elevation_time': activity['max_elevation_time'],
                            'max_elevation': activity['max_elevation'],
                            'end_time': activity['end_time'],
                            'duration': activity['duration'],
                            'status': activity['activity_status'],
                            'priority': activity['priority'],
                            'updated_at': activity['updated_at']
                        },
                        'asignaciones': []
                    }
                self.activities[activity['activity_id']]['asignaciones'].append({
                    'id': activity['task_id'],
                    'is_active': activity['is_active'],
                    'antenna_id': activity['antenna_id'],
                    'antenna_code': activity['antenna_code'],
                    'antenna_name': activity['antenna_name'],
                    'is_confirmed': activity['is_confirmed'],
                    'assigned_at': activity['assigned_at'],
                    'confirmed_at': activity['confirmed_at'],
                    'config_number': activity['config_number'],
                    'updated_at': activity['updated_at'],
                    'last_sent_at': activity['last_sent_at'],
                    'send_status': activity['send_status']
                })

    def to_dict(self) -> dict:
        """Return all Activities in a dict."""
        return self.activities

class Task():
    """Clase Task"""
    def __init__(self, activity: dict, task: dict):
        """Constructor of the Task class"""
        self.original_task = task
        self.activity = activity
        self.task = {}

    def task_add(self):
        """
        Create a task for adding a new activity.

        Fields:
        - "task_id", "type": "string"
        - "action", "type": "string" 
        - "antenna_id", "type": ["null", "string"], "default": null 
        - "satellite", "type": ["null", "string"], "default": null 
        - "norad_id", "type": ["null", "string"], "default": null 
        - "config_id", "type": ["null", "int"], "default": null 
        - "start", "type": ["null", "string"], "default": null 
        - "end", "type": ["null", "string"], "default": null 
        - "prepass_seconds", "type": ["null", "int"], "default": null 
        - "postpass_seconds", "type": ["null", "int"], "default": null
        
        """
        self.task = {
            "task_id": self.original_task.get("id"),              # 'id': 'ASG007b'
            "satellite": self.activity.get("satellite_name"),     # 'satellite_name': 'SAOCOM-1B'
            "action": 'ADD',
            "antenna_id": self.original_task.get("antenna_code"), # 'antenna_id': 'ANT003', 'antenna_code': 'ANTVSTM01', 'antenna_name': 'ANTENA 13.5'
            "norad_id": self.activity.get("satellite_id"),        # 'satellite_id': '27424'
            "config_id": self.original_task.get("config_number"), # 'config_number': 9
            "start": self.activity.get("start_time"),             # 'start_time': '2025-07-16T16:16:00Z'
            "end": self.activity.get("end_time"),                 # 'end_time': '2025-07-16T16:17:00Z'
            "prepass_seconds": self.original_task.get("prepass_seconds", 120),
            "postpass_seconds": self.original_task.get("postpass_seconds", 60)
        }

    def task_delete(self):
        """Create a task for adding a new activity."""
        self.task = {
            "task_id": self.original_task.get("id"),
            "action": 'DELETE'
        }

    def task_purge(self):
        """Create a task for purging an activity."""
        self.task = {
            "task_id": self.original_task.get("id"),
            "action": 'PURGE'
        }

    def to_dict(self):
        """Return Task in a dict."""
        return self.task

class Plann():
    """Clase PLAN"""
    def __init__(self, plann: dict, source: str = "sender", plann_type: str = "PLANN", antenna_id: str = None):
        """
        Constructor of the PLAN class
        
        Fields:
        - "name": "message_type","type": "string"
        - "name": "antenna_id", "type": "string"
        - "name": "timestamp", "type": "string"
        - "name": "source", "type": "string"
        - "name": "plan", "type": {"type": "array"}
        - "name": "tles", "type": {"type": "array", "default": [] }
        """
        self.plann = {
            "id": plann.get("id"),
            "message_type": plann_type,
            "antenna_id": antenna_id,
            "timestamp": datetime.utcnow().isoformat(),
            "source": source,
            "plan": plann.get("plan", []),
            "tles": plann.get("tles", [])
        }

    def to_dict(self):
        """Return PLAN in a dict."""
        return self.plann

class TLE():
    """Clase TLE"""
    def __init__(self, norad_id: str, satellite_name: str, tle_line1: str, tle_line2: str, timestamp: datetime):
        """Constructor of the Task class"""
        self.tle = {
            "norad_id": norad_id,
            "satellite_name": satellite_name,
            "tle_line1": tle_line1,
            "tle_line2": tle_line2,
            "timestamp": timestamp.isoformat()
        }

    def to_dict(self):
        """Return TLE in a dict."""
        return self.tle
