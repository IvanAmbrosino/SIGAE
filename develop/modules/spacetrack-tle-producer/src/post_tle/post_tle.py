"""Funcion que produce mensajes con los nuevos TLEs"""
import logging
#from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka import SerializingProducer
from confluent_kafka.serialization import StringSerializer
from config_manager import ConfigManager

class PostTle():
    """Clase generadora de tles"""
    def __init__(self, logger : logging.Logger = None):
        self.config_manager     = ConfigManager()
        self.kafka_config       = self.config_manager.config["kafka_config"]
        self.producer           = None
        self.logger             = logger
        self.conect_kafka_producer() # Creamos el producer una sola vez al iniciar la clase

    def conect_kafka_producer(self):
        """Conexion con kafka"""
        # Configuración del schema registry
        schema_registry_conf = {
            'url': self.kafka_config["schema_registry_url"]     # URL del Schema Registry
        }
        schema_registry_client = SchemaRegistryClient(schema_registry_conf)
        schema_string_config = self.config_manager.read_config_string(self.kafka_config["schema_file"])
        avro_serializer = AvroSerializer(schema_registry_client, schema_string_config)

        # Configuración del serializador Avro
        kafka_producer_conf = {
        'bootstrap.servers':                     self.kafka_config["bootstrap_servers"],                     # Brokers de Kafka
        'client.id':                             self.kafka_config["client_id"],                             # ID del cliente
        'enable.idempotence':                    self.kafka_config["enable_idempotence"],                    # ← importante, evita duplicados
        'acks':                                  self.kafka_config["acks"],                                  # ← asegura confirmación de los 3 brokers en las replicas
        'retries':                               self.kafka_config["retries"],                               # intenta reintentos controlados
        'max.in.flight.requests.per.connection': self.kafka_config["max_in_flight_requests_per_connection"], # seguro con idempotencia
        'key.serializer': StringSerializer('utf_8'),                                                         # Serializador de claves (en este caso, String)
        'value.serializer': avro_serializer                                                                  # Serializador de valores (en este caso, Avro)
        }

        if not self.producer:
            self.producer = SerializingProducer(kafka_producer_conf)

    def kafka_producer(self, message : dict, topic : str):
        """Funcion que productora de mensajes"""
        def delivery_report(err, msg):
            if err is not None:
                self.logger.error(f'Message delivery failed: {err}')
            else:
                self.logger.info(f'Message delivered to {msg.topic()} [{msg.partition()}]')

        self.producer.produce(topic =       topic,
                              key =         topic,
                              value =       message,
                              on_delivery = delivery_report)
        self.producer.poll(0)           # permite procesar callbacks de forma no bloqueante
        self.producer.flush(timeout=5)  # espera a que se envíen todos los mensajes pendientes
