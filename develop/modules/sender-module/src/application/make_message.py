"""Clase que crea mensajes para el modulo sender."""
from domain.class_domain import Task, Plann, TLE

class MakeMessage:
    """Class to create messages for the sender module."""

    def make_message_add(self, activity: dict, task: dict) -> dict:
        """Crea un mensaje de tipo ADD para la planificacion."""
        maker_task = Task(activity, task).task_add()
        return maker_task.to_dict()

    def make_message_delete(self, activity: dict, task: dict) -> dict:
        """Crea un mensaje de tipo ADD para la planificacion."""
        maker_task = Task(activity, task).task_delete()
        return maker_task.to_dict()

    def make_message_purgue(self, activity: dict, task: dict) -> dict:
        """Crea un mensaje de tipo ADD para la planificacion."""
        maker_task = Task(activity, task).task_purge()
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
