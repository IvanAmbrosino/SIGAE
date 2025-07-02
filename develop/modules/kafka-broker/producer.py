# avro_producer.py
from time import sleep
from datetime import datetime
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka import SerializingProducer
from confluent_kafka.serialization import StringSerializer

# Configuración del schema registry y Kafka
schema_registry_conf = {'url': 'http://localhost:8081'}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)

# Cargamos el esquema desde archivo
with open("tle_schema.json",'r',encoding='utf-8') as f:
    schema_str = f.read()

# Serializer
avro_serializer = AvroSerializer(schema_registry_client, schema_str)

producer_conf = {
    'bootstrap.servers': 'localhost:19092',
    'key.serializer': StringSerializer('utf_8'),
    'value.serializer': avro_serializer
}

producer = SerializingProducer(producer_conf)
try:
    while True:
        # Mensaje
        message = {
            "satellite_name": "ISS (ZARYA)",
            "line1": "1 25544U 98067A   20129.54791435  .00001264  00000-0  29621-4 0  9993",
            "line2": "2 25544  51.6452 354.1294 0005377  94.3673  17.0730 15.49458120223269",
            "timestamp": datetime.now()
        }
        producer.produce(topic="ISS", key=message["satellite_name"], value=message)
        producer.flush()
        print(f"📡 Enviado mensaje: {message['satellite_name']} a las {message['timestamp']}")
        sleep(1)
except KeyboardInterrupt:
    pass
