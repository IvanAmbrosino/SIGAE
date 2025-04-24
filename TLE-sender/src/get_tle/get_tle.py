"""Modulo que se encarga de obtener el TLE desde la interfaz de Kafka"""
import json
import time
from datetime import datetime, timedelta
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable, KafkaError

class KafkaConnector:
    """Clase consumidor de Kafka encargada de obtener los TLEs"""
    def __init__(self, config_file,logger):
        self.config = self._load_config(config_file)
        self.consumer = None
        self.logger = logger

    def _load_config(self, config_file) -> dict:
        """Carga la configuración desde un archivo JSON."""
        with open(config_file, 'r',encoding='utf-8') as f:
            return json.load(f)["get_tle"]

    def connect_to_kafka(self) -> KafkaConsumer:
        """Intenta conectarse a Kafka. Reintenta en caso de fallo."""
        while True:
            try:
                self.consumer = KafkaConsumer(
                    bootstrap_servers=self.config['bootstrap_servers'],
                    group_id=self.config['group_id'],
                    auto_offset_reset=self.config['auto_offset_reset'],  # Se reanuda desde el último mensaje leído
                    enable_auto_commit=True,  # Kafka almacena automáticamente los offsets
                )
                self.logger.info("Connected to Kafka successfully.")
                return self.consumer
            except (NoBrokersAvailable,KafkaError) as e:
                self.logger.error(f"Failed to connect to Kafka: {e}. Retrying in 5 seconds...")
                time.sleep(5)

    def get_message(self,list_satellites):
        """
        Obtiene un mensaje de Kafka.
        Recorre la lista de satelites, se suscribe a cada uno de ellos y obtiene el ultimo TLE.
        Devuelve un stream de "dicts" de los ultimos TLEs que van llegando.
        """
        self.connect_to_kafka()
        try:
            lista_suscripciones = [f"{satelite.split(';')[0]}" for satelite in list_satellites]
            self.consumer.subscribe(lista_suscripciones)
            while True:
                message_batch = self.consumer.poll(timeout_ms=10)
                if message_batch:
                    for _, messages in message_batch.items():
                        for message in messages:
                            yield json.loads(message.value.decode('utf-8'))
        except KafkaError as e:
            self.logger.error(f"Error consuming messages: {e}. Reconnecting...")
        finally:
            self.consumer.close()

    def get_bulk_message(self,list_satellites,awaiting_seconds=10) -> list:
        """
        Obtiene un mensaje de Kafka.
        Recorre la lista de satelites, se suscribe a cada uno de ellos.
        Obtiene todos los TLE que no se recibieron. Una funcion que se llama al inicio del programa.
        De todos los mensajes, compara y obtiene los que tengan el mayor timestamp. (ese valor tiene que existir)
        """
        self.connect_to_kafka()
        dict_tle,time_last_message = {}, datetime.now()
        try:
            lista_suscripciones = [f"{satelite.split(';')[0]}" for satelite in list_satellites]
            self.consumer.subscribe(lista_suscripciones)
            while True:
                message_batch = self.consumer.poll(timeout_ms=100)
                if message_batch:
                    for _, messages in message_batch.items():
                        for message in messages:
                            get_tle = json.loads(message.value.decode('utf-8'))
                            get_tle["timestamp"] = message.timestamp # En el caso que el tle no tenga el valor de timestamp en el campo value.
                            dict_tle.setdefault(get_tle["name"], []).append(get_tle)
                            self.logger.info(f'load tle {get_tle["name"]} date: {get_tle["line1"].split()[3].split(".")[0]} timestamp: {get_tle["timestamp"]}\n {json.loads(message.value.decode("utf-8"))}')
                            time_last_message = datetime.now() # Guarda el momento que se obtiene el ultimo mensaje
                if datetime.now() - time_last_message > timedelta(seconds=awaiting_seconds):
                    if not dict_tle:
                        return []
                    return [max(tles_list, key=lambda x: x["timestamp"]) for _, tles_list in dict_tle.items()] # Retorna la lista de los ultimos TLEs.
        except KafkaError as e:
            self.logger.error(f"Error consuming messages: {e}. Reconnecting...")
        finally:
            self.consumer.close()
        return []
