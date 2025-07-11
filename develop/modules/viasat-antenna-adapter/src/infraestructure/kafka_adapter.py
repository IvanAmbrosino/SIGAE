"""Modulo que se encarga de obtener el TLE desde la interfaz de Kafka"""
import time
import logging
from confluent_kafka import KafkaError as ConfluentKafkaError
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import StringDeserializer
from confluent_kafka import DeserializingConsumer

class KafkaConnector:
    """Clase consumidor de Kafka encargada de obtener los TLEs"""
    def __init__(self, kafka_config: dict, logger:logging):
        self.logger             = logger
        self.config             = kafka_config
        self.consumer           = None
        self.retry_connection() # Se conecta a Kafka y suscribe a los topics disponibles

    def retry_connection(self):
        """Intenta conectarse a Kafka y suscribirse a los topics disponibles."""
        for attempt in range(self.config['max_retries']):
            try:
                if self.consumer:
                    self.logger.warning("Cerrando consumidor Kafka anterior.")
                    self.consumer.close()
                self.connect_to_kafka() # Se conecta una sola vez
                self.suscribe_topics()  # Se suscribe a los topicos disponibles
                break
            except ConfluentKafkaError as e:
                self.logger.warning(f"[Intento {attempt + 1}] Error al obtener metadata: {e}.\
                                    Reintentando en {self.config['waiting_time']} segundos...")
                time.sleep(self.config['waiting_time'])
        else:
            self.logger.error("No se pudo obtener metadata de Kafka después de varios intentos. Abortando.")
            raise RuntimeError("Fallo al conectarse a Kafka y obtener metadata")


    def connect_to_kafka(self):
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
        except ConfluentKafkaError as e:
            self.logger.error(f"Failed to connect to Kafka: {e}. Retrying in 5 seconds...")

    def commmit_message(self,message):
        """Funcion que realiza el commit manual del mensaje"""
        self.consumer.commit(message=message)

    def suscribe_topics(self):
        """Funcion que se suscribe a los topicos disponibles en el broker"""
        # Recorremos el listado de satelites y nos suscribimos a los que esten disponibles en el broker
        # Tener en cuenta que si intentamos suscribirnos a un topico que no existe lanza error
        list_topics = ["TLE","PLAN"]
        self.consumer.subscribe(list_topics)

    def get_message(self):
        """
        Obtiene un mensaje de Kafka.
        Devuelve un stream de tuplas (Message, Message.value()) de los ultimos Mensajes que van llegando.
        """
        try:
            while True:
                message= self.consumer.poll(timeout=1.0)
                if message:
                    self.logger.debug("NEW MESSAGE: %s",message.value())
                    yield message, message.value()
        except ConfluentKafkaError as e:
            self.logger.error(f"Error consuming messages: {e}. Reconnecting...")
