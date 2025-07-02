# avro_consumer.py
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import StringDeserializer
from confluent_kafka import DeserializingConsumer

# Config
schema_registry_conf = {'url': 'http://localhost:8081'}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)

# Avro Deserializer
avro_deserializer = AvroDeserializer(schema_registry_client)

consumer_conf = {
    'bootstrap.servers': 'localhost:39092',
    'group.id': 'tle-avro-consumer',
    'auto.offset.reset': 'earliest',
    'key.deserializer': StringDeserializer('utf_8'),
    'value.deserializer': avro_deserializer
}

consumer = DeserializingConsumer(consumer_conf)
consumer.subscribe(["tle-topic-1"])

print("👂 Esperando mensajes...")

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        value = msg.value()
        if value is not None:
            print(f"📡 Satellite: {value['satellite_name']} Timestamp: {value['timestamp']}")
            print(f"  Line1: {value['line1']}")
            print(f"  Line2: {value['line2']}")
except KeyboardInterrupt:
    pass
finally:
    consumer.close()
