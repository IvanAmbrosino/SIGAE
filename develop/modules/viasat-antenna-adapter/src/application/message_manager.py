"""Modulo que procesa mensajes entrantes de Kafka."""
import logging

class MessageManager:
    """Clase para procesar mensajes entrantes de Kafka."""
    def __init__(self,logger: logging):
        self.logger = logger

    def process_message(self, msg: dict, ):
        """Procesa los mensajes recibidos de Kafka y determina su tipo para poder ser procesado."""
        if msg["type"] == "tle":
            #if validar_tle(msg):
                # Validar si es para la antena - En caso contrario corta el proceso
                # Validar el CRC, epoch contra fecha actual, etc.
                # Validar si es mas nuevo que el ultimo TLE - Comparar en la BD (en caso contrario no lo procesa)
            #make_tle_file(msg)
            #send_tle_file(msg)
            pass
        elif msg["type"] == "plan":
            #validar_plan(msg)
                # Validar si es para la antena - En caso contrario corta el proceso
                # Validar los horarios y que no se superponga con las otras planificaciones que estan en la BD
                # Validar que el satelite tenga TLE actualizado
                # Validar que la antena este disponible
            #save_plan_in_db(msg)
                # Guarda o actualiza la planificacion en la BD
            #make_plann_file(msg)
                # Validar que el archivo de planificacion este bien formado
            #send_plann_file(msg)
                # Envia el archivo de planificacion a la antena
                # Validar que el archivo sea Aceptado por la antena
                # Hace el commit del mensaje a kafka
            pass
        elif msg["type"] == "plan+tles":
            #validar_plan_con_tle(msg)
                # Validar si es para la antena - En caso contrario corta el proceso
                # Validar los horarios y que no se superponga con las otras planificaciones que estan en la BD
                # Validar que el satelite tenga TLE actualizado
                # Validar que la antena este disponible
            #make_tle_file(msg)
            #send_tle_file(msg) # primero debe enviar el TLE
            #make_plann_file(msg)
            #send_plann_file(msg)
            pass
