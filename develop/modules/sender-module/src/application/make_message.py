"""Clase que crea mensajes para el modulo sender."""


class MakeMessage:
    """Class to create messages for the sender module."""

    def make_plann_message(self, activities):
        """Create a message from the given plan."""
        message = {
            "type": "NEWPLANN",
            "plan": activities
        }
        return message

    def make_ack_message(self, plan_id):
        """Create an acknowledgment message for the given plan ID."""
        message = {
            "type": "ACK",
            "id": plan_id
        }
        return message
