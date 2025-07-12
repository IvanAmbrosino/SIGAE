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
# Lista de TLEs de ejemplo
tle_messages = [
    {
        "satellite_name": "ISS",
        "line1": "1 25544U 98067A   24185.18437500  .00016717  00000+0  10270-3 0  9000",
        "line2": "2 25544  51.6448  18.5343 0001567  74.9494 285.1856 15.50773339  1782"
    },
    {
        "satellite_name": "AQUA",
        "line1": "1 27424U 02022A   24185.20833333  .00000058  00000+0  24842-4 0  9991",
        "line2": "2 27424  98.2002 209.5112 0001090  91.2677 268.8644 14.57109462226089"
    },
    {
        "satellite_name": "LANDSAT-8",
        "line1": "1 39084U 15001A   24185.20200000  .00000100  00000+0  12345-4 0  9999",
        "line2": "2 39084  98.2100 210.0000 0001200  85.9000 275.0000 14.57120000000000  1234"
    },
    {
        "satellite_name": "ISS",
        "line1": "1 25544U 98067A   24185.19000000  .00017000  00000+0  10280-3 0  9001",
        "line2": "2 25544  51.6450  18.5300 0001570  75.0000 285.0000 15.50800000  1783"
    },
    {
        "satellite_name": "AQUA",
        "line1": "1 27424U 02022A   24185.21000000  .00000060  00000+0  24850-4 0  9992",
        "line2": "2 27424  98.2010 209.5100 0001100  91.2700 268.8600 14.57110000  9992"
    }
]
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
    for message in tle_messages:
        producer.produce(topic=TOPIC, key=message["satellite_name"], value=message)
        print(f"Mensaje enviado al topic {TOPIC}: {message}")
    producer.flush()
    print("Todos los mensajes enviados correctamente.")

if __name__ == "__main__":
    main()
