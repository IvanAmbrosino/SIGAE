"""Clase que crea mensajes para el modulo sender."""
import logging
from datetime import datetime, timedelta
from infraestructure.config_manager import ConfigManager # pylint: disable=import-error
from domain.class_domain import Task, Plann, TLE # pylint: disable=import-error

class MakeMessage:
    """Class to create messages for the sender module."""
    def __init__(self, logger: logging):
        self.logger = logger
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()

    def make_message_add(self, activity: dict, task: dict) -> dict:
        """Crea un mensaje de tipo ADD para la planificacion."""
        #self.logger.debug("Armado de mensaje ADD con: \n Activity: %s \n Task: %s", activity, task)
        maker_task = Task(activity, task)
        maker_task.task_add()
        return maker_task.to_dict()

    def make_message_delete(self, activity: dict, task: dict) -> dict:
        """Crea un mensaje de tipo DELETE para la planificacion."""
        #self.logger.debug("Armado de mensaje DELETE con: \n Activity: %s \n Task: %s", activity, task)
        maker_task = Task(activity, task)
        maker_task.task_delete()
        return maker_task.to_dict()

    def make_message_purgue(self, activity: dict, task: dict) -> dict:
        """Crea un mensaje de tipo PURGE para la planificacion."""
        #self.logger.debug("Armado de mensaje PURGE con: \n Activity: %s \n Task: %s", activity, task)
        maker_task = Task(activity, task)
        maker_task.task_purge()
        return maker_task.to_dict()

    def make_plann_messages(self, plan: dict) -> dict:
        """
        Create a message from the given plan for all antennas.

        Return List[Plann_to_send-ANTX]
        """
        plan_to_send = []
        for antenna, tasks in plan.items():
            plann_type = "PLANN" # configurable
            for task in tasks:
                if not self.validate_init_time(task.get("start").isoformat()):
                    self.logger.info("Actividad muy proxima en el tiempo, mandando Activiad con TLE")
                    plann_type = "PLANNTLE" # configurable
                    # Obtener el ultimo TLE de la BD
                    # armar el mensaje
                    # Agregar en lista 'tles'

            maker_plann = Plann(
                plann=tasks,
                plann_type=plann_type,
                antenna_id=antenna
                )
            plan_to_send.append(maker_plann.to_dict())
        return plan_to_send

    def make_tle_message(self, tle: dict) -> dict:
        """Create a TLE message."""
        maker_tle = TLE(norad_id=tle.get("norad_id"),
                        satellite_name=tle.get("satellite_name"),
                        tle_line1=tle.get("tle_line1"),
                        tle_line2=tle.get("tle_line2"),
                        timestamp=datetime.utcnow())
        return maker_tle.to_dict()

    def validate_init_time(self, task_start_time: datetime) -> bool:
        """Validate the initial time format."""
        if task_start_time < datetime.utcnow() + timedelta(minutes= self.config['app']['min_hours_tle_required']):
            return False
        return True
