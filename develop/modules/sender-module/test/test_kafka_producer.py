"""Funcion que produce mensajes con los nuevos TLEs"""
import random
import pprint 
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
    tle = True
    plann = True
    if tle:
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
            "norad_id": "27424",
            "satellite_name": "AQUA",
            "line1": "1 27424U 02022A   25196.49513346  .00000619  00000-0  13513-3 0  9995",
            "line2": "2 27424  98.3792 155.2050 0001077  54.3075  55.4292 14.61346150234126",
            "timestamp": "2025-07-14T13:16:14Z"
        }

        pprint.pprint(tle_random)
        PT.kafka_producer(message= tle_random, topic= 'TLE')
    if plann:
        PT = PostTle()
        PLANN_SCHEMA = """{
                "type": "record",
                "name": "FullPlanMessage",
                "namespace": "com.tuempresa.planificacion",
                "doc": "Mensaje completo de planificación de una antena",
                "fields": [
                    { "name": "message_type","type": "string" },
                    { "name": "antenna_id", "type": "string" },
                    { "name": "timestamp", "type": "string" },
                    { "name": "source", "type": "string" },
                    {
                    "name": "plan",
                    "type": {
                        "type": "array",
                        "items": {
                        "name": "PasePlanificado",
                        "type": "record",
                        "fields": [
                            { "name": "task_id", "type": "string" },
                            { "name": "action", "type": "string" },
                            { "name": "antenna_id", "type": "string" },
                            { "name": "satellite", "type": "string" },
                            { "name": "norad_id", "type": "string" },
                            { "name": "config_id", "type": "int" },
                            { "name": "start", "type": "string" },
                            { "name": "end", "type": "string" },
                            { "name": "prepass_seconds", "type": "int", "default": 120 },
                            { "name": "postpass_seconds", "type": "int", "default": 60 }
                        ]
                        }
                    }
                    }
                ]
                }
                """
        PT.conect_kafka_producer(schema=PLANN_SCHEMA)
        planificacion_random = {
                                "message_type": "PLANN",
                                "antenna_id": "ANTENA_DEFAULT",
                                "timestamp": "2025-07-11T14:00:00Z",
                                "source": "planificador_automatico",
                                "plan": [
                                    {
                                    "task_id": "SAOCOM1B_ANTENA_6_2025_193_130002",
                                    "satellite": "SAOCOM-1B",
                                    "action": "ADD",
                                    "antenna_id": "VIASAT",
                                    "norad_id": "43641",
                                    "config_id": 10,
                                    "start": "2025-07-16T15:16:00Z",
                                    "end": "2025-07-16T15:17:00Z",
                                    "prepass_seconds": 120,
                                    "postpass_seconds": 60
                                    },
                                    {
                                    "task_id": "AQUA_ANTENA_6_2025_193_130003",
                                    "satellite": "AQUA",
                                    "action": "ADD",
                                    "antenna_id": "VIASAT",
                                    "norad_id": "27424",
                                    "config_id": 9,
                                    "start": "2025-07-16T16:16:00Z",
                                    "end": "2025-07-16T16:17:00Z",
                                    "prepass_seconds": 120,
                                    "postpass_seconds": 60
                                    }
                                ]
                            }
        pprint.pprint(planificacion_random)
        PT.kafka_producer(message= planificacion_random, topic= 'PLANN')
