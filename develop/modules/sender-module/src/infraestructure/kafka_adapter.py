"""Modulo adaptador con las funciones get y send messages a kafka"""
import logging
from confluent_kafka import KafkaError as ConfluentKafkaError
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer, AvroSerializer
from confluent_kafka.serialization import StringDeserializer, StringSerializer
from confluent_kafka import DeserializingConsumer, SerializingProducer

from infraestructure.config_manager import ConfigManager

class KafkaConnector:
    """Clase que maneja las conexiones a kafka"""
    def __init__(self, kafka_config: dict, topic: str, logger:logging, consumer: bool, producer: bool):
        self.logger             = logger
        self.config             = kafka_config
        self.create_consumer    = consumer
        self.create_producer    = producer
        self.topic              = topic
        self.consumer           = None
        self.config_manager     = ConfigManager()
        self.producers          = {}
        self.serializers        = {}
        self.connect() # Se conecta a Kafka y suscribe a los topics disponibles

    def connect(self):
        """Realiza todas las conexiones a kafka."""
        try:
            if self.create_consumer:
                if self.consumer:
                    self.logger.warning("Cerrando consumidor Kafka anterior.")
                    self.consumer.close()
                self.connect_to_kafka_consumer() # Se conecta una sola vez
                self.suscribe_topics()  # Se suscribe a los topicos disponibles
            if self.create_producer:
                if self.producers:
                    self.logger.warning("Conexion de Productor abierta al intentar crear una nueva conexion.")
                self.connect_to_kafka_producer() # Se conecta una sola vez con todos los schemas
        except ConfluentKafkaError as e:
            self.logger.warning("Error al obtener metadata: %s.",e,)

    def connect_to_kafka_producer(self):
        """
        Conexion a kafka para productores
            - Crea una conexion para enviar mensajes con el schema sender_plann
            - Crea una conexion para enviar mensajes con el schema sender_plann_tle
        
        Registra las conexiones por tipo de schema, guardando en "self.producers[schema_type] = SerializingProducer"
        """
        # Configuración del schema registry
        schema_registry_conf = {
            'url': self.config["schema_registry_url"]    # URL del Schema Registry
        }
        schema_registry_client = SchemaRegistryClient(schema_registry_conf)
        self.serializers = {
            "sender_plann": AvroSerializer(schema_registry_client,
                                           self.config_manager.read_config_string(self.config['schema']['sender_plann'])),
            "sender_plann_tle": AvroSerializer(schema_registry_client,
                                               self.config_manager.read_config_string(self.config['schema']['sender_plann_tle'])),
        }

        # Configuración del serializador Avro
        for schema_type, serializer in self.serializers.items():
            kafka_producer_conf = {
                'bootstrap.servers':    self.config['bootstrap_servers'],
                'client.id':            self.config['group_id'],
                'enable.idempotence':   True,
                'acks':                 "all",
                'retries':              5,
                'key.serializer':       StringSerializer('utf_8'),
                'value.serializer':     serializer,
                'max.in.flight.requests.per.connection': 5
            }
            self.producers[schema_type] = SerializingProducer(kafka_producer_conf)

    def connect_to_kafka_consumer(self):
        """Intenta conectarse a Kafka como consumidor"""
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
        list_topics = self.topic
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

    def send_message(self, topic: str, key: str, value: dict, schema_type: str):
        """
        Funcion que productora de mensajes
            - schema_type: "sender_plann" | "sender_plann_tle"
        """
        if schema_type not in self.producers:
            raise ValueError(f"Schema type '{schema_type}' no inicializado.")

        def delivery_report(err, msg):
            if err is not None:
                self.logger.error(f'Message delivery failed: {err}')
            else:
                self.logger.info(f'Message delivered to {msg.topic()} [{msg.partition()}]')

        producer = self.producers[schema_type]
        producer.produce(topic =       topic,
                              key =         key,
                              value =       value,
                              on_delivery = delivery_report)
        producer.poll(0)           # permite procesar callbacks de forma no bloqueante
        producer.flush(timeout=5)  # espera a que se envíen todos los mensajes pendientes
