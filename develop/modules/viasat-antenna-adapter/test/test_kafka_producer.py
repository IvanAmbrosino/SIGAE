"""Funcion que produce mensajes con los nuevos TLEs"""
import random
from datetime import datetime
#from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka import SerializingProducer
from confluent_kafka.serialization import StringSerializer

class PostTle():
    """Clase generadora de tles"""
    def __init__(self):
        self.producer = None

    def conect_kafka_producer(self,schema):
        """Conexion con kafka"""
        # Configuración del schema registry
        schema_registry_conf = {
            'url': "http://localhost:8081"    # URL del Schema Registry
        }
        schema_registry_client = SchemaRegistryClient(schema_registry_conf)
        schema_string_config = schema
        avro_serializer = AvroSerializer(schema_registry_client, schema_string_config)

        # Configuración del serializador Avro
        kafka_producer_conf = {
        'bootstrap.servers': "localhost:19092,localhost:29092,localhost:39092", # Brokers de Kafka
        'client.id': "tle-consumer", # ID del cliente
        'enable.idempotence': True, # ← importante, evita duplicados
        'acks': "all", # ← asegura confirmación de los 3 brokers en las replicas
        'retries': 5, # intenta reintentos controlados
        'max.in.flight.requests.per.connection': 5,
        'key.serializer': StringSerializer('utf_8'),# Serializador de claves (en este caso, String)
        'value.serializer': avro_serializer # Serializador de valores (en este caso, Avro)
        }

        if not self.producer:
            self.producer = SerializingProducer(kafka_producer_conf)

    def kafka_producer(self, message : dict, topic : str):
        """Funcion que productora de mensajes"""
        def delivery_report(err, msg):
            if err is not None:
                print(f'Message delivery failed: {err}')
            else:
                print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

        self.producer.produce(topic =       topic,
                              key =         topic,
                              value =       message,
                              on_delivery = delivery_report)
        self.producer.poll(0)           # permite procesar callbacks de forma no bloqueante
        self.producer.flush(timeout=5)  # espera a que se envíen todos los mensajes pendientes

if __name__ == "__main__":
    PT = PostTle()
    TLE_SCHEMA = """{
            "namespace": "com.example.tle",
            "type": "record",
            "name": "TLEData",
            "fields": [
                { "name": "message_type", "type": "string" },
                { "name": "norad_id", "type": "string" },
                { "name": "satellite_name", "type": "string" },
                { "name": "line1", "type": "string" },
                { "name": "line2", "type": "string" },
                { "name": "timestamp", "type": "string" }
            ]
            }"""
    PT.conect_kafka_producer(TLE_SCHEMA)

    tle_random = {
        "message_type": "TLE",
        "norad_id": "43641",
        "satellite_name": "SAOCOM 1A",
        "line1": "1 27424U 02022A   25195.59461420  .00000577  00000-0  12652-3 0  9996",
        "line2": "2 27424  98.3792 154.2929 0001113  53.9678   1.0769 14.61344720233952",
        "timestamp": "2025-07-14T14:16:14Z"
    }

    print(tle_random)
    PT.kafka_producer(message= tle_random, topic= 'TLE')
