"""Init module for sending and receiving ack messages."""
import os
import logging
import logging.handlers
import threading
import time

from infraestructure.config_manager import ConfigManager # pylint: disable=import-error
from infraestructure.kafka_adapter import KafkaConnector # pylint: disable=import-error
from application.planning_manager import PlanningManager # pylint: disable=import-error
from application.make_message import MakeMessage # pylint: disable=import-error

PENDING_ACK = {}
PENDING_ACK_LOCK = threading.Lock()
THREADS = {}


logger = logging.getLogger("Main")

class SenderModule:
    """Main class for Sender Module."""
    def __init__(self):
        """
        Module responsible for receiving event messages, sending the schedule and waiting for the ACK message

        Uses 3 processing threads:

            - Consumes messages from the "EVENTS" topic.When a new event "new_plann" arrives, 
              it queries the database, assembles the message, and sends it to the "PLANN "topic.

            - It consists of a thread in charge of waiting for the arrival of an "ACK" message 
              related to the message sent.

            - Finally, a thread that checks the sent messages and verifies their "timeout".
              If the timeout is exceeded, a "warning" must be sent and the "message resent".
        """
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()              # Se cargan las configuracioens

        self.script_dir = os.path.dirname(os.path.abspath(__file__)) # Directory of the script
        self.kafka_config = self.config['kafka']                     # Kafka connection configuration
        self.app_config = self.config['app']                         # Application configuration
        self.logs_config = self.config['logs']                       # Logging configuration
        self.load_logger()                                           # Carga la configuracion de los logs
        self.planning_manager = PlanningManager(logger=logger)       # Instancia del PlanningManager

        # Definimos los hilos y los guardamos
        if self.app_config["ack_check"]:
            THREADS['sender_thread'] = threading.Thread(target=self.sender_thread, daemon=True)
            THREADS['ack_listener_thread'] = threading.Thread(target=self.ack_listener_thread, daemon=True)
            THREADS['timeout_checker_thread'] = threading.Thread(target=self.timeout_checker_thread, daemon=True)

            for t in THREADS.values():
                t.start()

            self.thread_watcher() # El proceso principal es el Supervisor

        else:
            self.sender_thread()  # Si no se chequea ACK, se ejecuta el hilo de envio como proceso principal

    def sender_thread(self):
        """Hilo que envia los mensajes de planificacion."""
        # aca se puede hacer un wile true donde se obtienen mensajes
        # pero si se pasa cierto tiempo, hace una consulta manual
        topic = self.kafka_config["topic"]["event_topic"]
        sender_kafka_adapter = KafkaConnector(self.kafka_config, topic, logger)
        logger.info("Iniciando hilo de envio de mensajes: SENDER-THREAD")
        for message, message_value in sender_kafka_adapter.get_message(topic= 'EVENTS'):
            #try:
            if message_value['type'] == "NEWPLANN":
                plan = self.planning_manager.obtener_proxima_planificacion() # Obtenemos la lista de planificacion a enviar
                message_to_send= MakeMessage().make_message(plan)            # Armamos el mensaje adecuado con toda la informacion
                sender_kafka_adapter.send_message(topic= 'PLANN',
                                                  key= 'PLANN',
                                                  value= message_to_send,
                                                  schema_type= 'sender_plann'
                                                  )
                with PENDING_ACK_LOCK:
                    PENDING_ACK[message_to_send["id"]] = {"timestamp": time.time(), "retries": 0}
            sender_kafka_adapter.commmit_message(message=message)
            #except Exception as e: # pylint: disable=broad-exception-caught
            #    logger.error("Fatal error en el proceso principal: %s",e)

    def ack_listener_thread(self):
        """Hilo que escucha los ACK de los mensajes enviados."""
        topic = self.kafka_config["topic"]["ack_topic"]
        ack_kafka_adapter = KafkaConnector(self.kafka_config, topic, logger)
        logger.info("Iniciando hilo de recepcion de mensajes: ACK-LISTENER-THREAD")
        for message, message_value in ack_kafka_adapter.get_message(topic= 'ACK'):
            with PENDING_ACK_LOCK:
                if message_value["id"] in PENDING_ACK:
                    del PENDING_ACK[message_value["id"]]
            ack_kafka_adapter.commmit_message(message=message)

    def timeout_checker_thread(self):
        """Hilo que revisa los Timeouts de los ACK que no se recibieron."""
        logger.info("Iniciando hilo que comprueba timeouts: TIMEOUT-CHECKER-THREAD")
        while True:
            #try:
            now = time.time()
            with PENDING_ACK_LOCK:
                for plan_id, info in list(PENDING_ACK.items()):
                    if now - info["timestamp"] > self.app_config["message_ack_timeout"]:
                        logger.error("Timeout para la planificacion: %s",plan_id)
                        # Deberia haber un reenvio de mensajes por aca
                        del PENDING_ACK[plan_id]
            time.sleep(5)
            #except Exception as e: # pylint: disable=broad-exception-caught
            #    logger.error("Fatal error en el proceso principal: %s",e)

    def thread_watcher(self):
        """Hilo supervisor de los demas hilos."""
        logger.info("Iniciando hilo supervisor: SUPERVISORD-THREAD")
        while True:
            #try:
            for name, t in list(THREADS.items()):
                if not t.is_alive():
                    logger.error("[WATCHER] Hilo %s cayó. Reiniciando...",name)
                    self.__start_thread(name, t._target)  # pylint: disable=protected-access
            time.sleep(5)
            #except Exception as e: # pylint: disable=broad-exception-caught
            #    logger.error("Fatal error en el proceso principal: %s",e)

    def __start_thread(self, name, target_func):
        t = threading.Thread(target=target_func, daemon=True)
        t.start()
        THREADS[name] = t

    def load_logger(self) -> None:
        """Load logger configuration."""
        try:
            if not logger.handlers:
                if self.logs_config['log_level']:
                    logger.setLevel(logging.getLevelName(self.logs_config['log_level'].upper()))
                else:
                    logger.setLevel(logging.INFO)
                handler = logging.handlers.RotatingFileHandler(
                    filename=(f'{self.script_dir}/{self.logs_config["folder"]}/{self.logs_config["filename"]}'),
                    mode='a', maxBytes=self.logs_config["size"],
                    backupCount= self.logs_config["rotation"],
                    encoding='utf-8')
                formatter = logging.Formatter(
                    "%(asctime) 15s - %(process)d - %(name)s -\
                        %(lineno)s - %(levelname)s - %(message)s")
                handler.setFormatter(formatter)
                logger.addHandler(handler)
        except TypeError as e:
            logger.error("error en la generacion de logs: %s",e)

if __name__ == "__main__":
    SenderModule()
