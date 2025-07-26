"""Clase que crea mensajes para el modulo sender."""
import logging
from domain.class_domain import Task, Plann, TLE # pylint: disable=import-error

class MakeMessage:
    """Class to create messages for the sender module."""
    def __init__(self, logger: logging):
        self.logger = logger

    def make_message_add(self, activity: dict, task: dict) -> dict:
        """Crea un mensaje de tipo ADD para la planificacion."""
        self.logger.debug("Armado de mensaje ADD con: \n Activity: %s \n Task: %s", activity, task)
        maker_task = Task(activity, task)
        maker_task.task_add()
        return maker_task.to_dict()

    def make_message_delete(self, activity: dict, task: dict) -> dict:
        """Crea un mensaje de tipo DELETE para la planificacion."""
        self.logger.debug("Armado de mensaje DELETE con: \n Activity: %s \n Task: %s", activity, task)
        maker_task = Task(activity, task)
        maker_task.task_delete()
        return maker_task.to_dict()

    def make_message_purgue(self, activity: dict, task: dict) -> dict:
        """Crea un mensaje de tipo PURGE para la planificacion."""
        self.logger.debug("Armado de mensaje PURGE con: \n Activity: %s \n Task: %s", activity, task)
        maker_task = Task(activity, task)
        maker_task.task_purge()
        return maker_task.to_dict()

    def make_plann_message(self, plan: dict) -> dict:
        """Create a message from the given plan."""
        #for task in plan.items():
        #    self.make_message_add(task['datos'], task['task'])

        maker_plann = Plann(plann=plan,
                            source="sender",
                            plann_type="PLANN",
                            antenna_id=plan.get("antenna_id"))

        return maker_plann.to_dict()

    def make_ack_message(self, plan_id):
        """Create an acknowledgment message for the given plan ID."""
