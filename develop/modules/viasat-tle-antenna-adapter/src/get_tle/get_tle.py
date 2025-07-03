"""Modulo que se encarga de obtener el TLE desde la interfaz de Kafka"""
import json
import time
import logging
from confluent_kafka import Consumer, KafkaError as ConfluentKafkaError
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import StringDeserializer
from confluent_kafka import DeserializingConsumer

class KafkaConnector:
    """Clase consumidor de Kafka encargada de obtener los TLEs"""
    def __init__(self, config_file: str, logger:logging, list_satellites: list):
        self.config             = self._load_config(config_file)
        self.list_satellites    = list_satellites
        self.logger             = logger
        self.consumer           = None
        #self.connect_to_kafka() # Se conecta una sola vez
        #self.suscribe_topics()  # Se suscribe a los topicos disponibles

        # Reintentos de conexion con kafka
        max_retries             = self.config['max_retries']
        delay                   = self.config['waiting_time']
        for attempt in range(max_retries):
            try:
                if self.consumer:
                    self.logger.warning("Cerrando consumidor Kafka anterior.")
                    self.consumer.close()
                self.connect_to_kafka() # Se conecta una sola vez
                self.suscribe_topics()  # Se suscribe a los topicos disponibles
                break
            except ConfluentKafkaError as e:
                self.logger.warning(f"[Intento {attempt + 1}] Error al obtener metadata: {e}. Reintentando en {delay} segundos...")
                time.sleep(delay)
        else:
            self.logger.error("No se pudo obtener metadata de Kafka después de varios intentos. Abortando.")
            raise RuntimeError("Fallo al conectarse a Kafka y obtener metadata")

    def _load_config(self, config_file) -> dict:
        """Carga la configuración desde un archivo JSON."""
        with open(config_file, 'r',encoding='utf-8') as f:
            return json.load(f)["get_tle"]

    def connect_to_kafka(self) -> Consumer:
        """Intenta conectarse a Kafka. Reintenta en caso de fallo."""
        # Config schema registry
        schema_registry_conf = {
            'url': self.config["schema_registry_url"] # URL del Schema Registry
            }
        schema_registry_client = SchemaRegistryClient(schema_registry_conf)
        avro_deserializer = AvroDeserializer(schema_registry_client)
        # Config consumer
        consumer_conf = {
            'bootstrap.servers':    self.config['bootstrap_servers'],
            'group.id':             self.config['group_id'],
            'auto.offset.reset':    self.config['auto_offset_reset'],
            'enable.auto.commit':   self.config['enable_auto_commit'],
            'key.deserializer':     StringDeserializer('utf_8'),
            'value.deserializer':   avro_deserializer
        }

        try:
            self.consumer = DeserializingConsumer(consumer_conf)
            self.logger.info("Connected to Kafka successfully.")
            return self.consumer
        except ConfluentKafkaError as e:
            self.logger.error(f"Failed to connect to Kafka: {e}. Retrying in 5 seconds...")

    def commmit_message(self,message):
        """Funcion que realiza el commit manual del mensaje"""
        self.consumer.commit(message=message)

    def suscribe_topics(self):
        """Funcion que se suscribe a los topicos disponibles en el broker"""
        # Consultamos el listado de topicos presente en el broker
        self.metadata = self.consumer.list_topics()
        self.topics = self.metadata.topics
        self.logger.debug("listado de topicos: %s",self.topics)

        # Recorremos el listado de satelites y nos suscribimos a los que esten disponibles en el broker
        # Tener en cuenta que si intentamos suscribirnos a un topico que no existe lanza error
        col = self.config["topic"] # Establece la columna de la cual sacara el topico
        list_norad_id = [f"{satelite.split(';')[col].replace(' ','_').strip()}" for satelite in self.list_satellites]
        self.logger.debug("Lista de satelites id %s",list_norad_id)
        list_suscriptions = []
        for key,_ in self.topics.items():
            if key in list_norad_id:
                list_suscriptions.append(key) # agregamos los topicos que existan
        self.logger.debug("Lista de suscripciones %s",list_suscriptions)

        # Finalmente nos suscribimos
        self.consumer.subscribe(list_suscriptions)

    def get_message(self):
        """
        Obtiene un mensaje de Kafka.
        Recorre la lista de satelites, se suscribe a cada uno de ellos y obtiene el ultimo TLE.
        Devuelve un stream de "dicts" de los ultimos TLEs que van llegando.
        """
        try:
            while True:
                message= self.consumer.poll(timeout=1.0)
                if message:
                    self.logger.debug("new message: %s",message.value())
                    yield message, message.value()
        except ConfluentKafkaError as e:
            self.logger.error(f"Error consuming messages: {e}. Reconnecting...")
