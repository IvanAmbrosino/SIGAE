import json
from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import StringSerializer

# Este script envía un mensaje de prueba al topic '_TLE' en Kafka utilizando Avro para la serialización del mensaje.
# Tambien se envia el esquema del mensaje al Schema Registry.

# Configuración
KAFKA_BOOTSTRAP_SERVERS = 'kafka-broker-1:9092'
SCHEMA_REGISTRY_URL = 'http://schema-registry:8081'
TOPIC = '_TLE'

# Esquema Avro
schema_str = '''{
  "type": "record",
  "name": "TLEMessage",
  "fields": [
    {"name": "satellite_name", "type": "string"},
    {"name": "line1", "type": "string"},
    {"name": "line2", "type": "string"}
  ]
}'''

# Mensaje de prueba
message = {
    "satellite_name": "ISS",
    "line1": "1 25544U 98067A   24185.18437500  .00016717  00000+0  10270-3 0  9000",
    "line2": "2 25544  51.6448  18.5343 0001567  74.9494 285.1856 15.50773339  1782"
}

def main():
    schema_registry_conf = {'url': SCHEMA_REGISTRY_URL}
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)
    avro_serializer = AvroSerializer(schema_registry_client, schema_str)

    producer_conf = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'key.serializer': StringSerializer('utf_8'),
        'value.serializer': avro_serializer
    }
    producer = SerializingProducer(producer_conf)
    producer.produce(topic=TOPIC, key=message["satellite_name"], value=message)
    producer.flush()
    print(f"Mensaje enviado al topic {TOPIC}:", message)

if __name__ == "__main__":
    main()
