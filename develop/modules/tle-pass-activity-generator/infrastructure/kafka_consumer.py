
import yaml
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import StringDeserializer
from confluent_kafka import DeserializingConsumer

from infrastructure.db import get_db_connection
from application.orchestrator import handle_tle_message
from infrastructure.logger import setup_logger


def load_config():
    with open('configs/config.yaml', 'r') as f:
        return yaml.safe_load(f)

def consume_tle_messages():
    config = load_config()
    logger = setup_logger(__name__)

    db_config = config['database']
    kafka_conf = config['kafka']
    schema_conf = config['schema_registry']

    schema_registry_conf = {'url': schema_conf['url']}
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)
    avro_deserializer = AvroDeserializer(schema_registry_client)

    consumer_conf = {
        'bootstrap.servers': kafka_conf['bootstrap_servers'],
        'group.id': kafka_conf['group_id'],
        'auto.offset.reset': 'earliest',
        'key.deserializer': StringDeserializer('utf_8'),
        'value.deserializer': avro_deserializer
    }

    consumer = DeserializingConsumer(consumer_conf)
    consumer.subscribe([kafka_conf['topic']])

    logger.info("Esperando mensajes de TLE...")
    try:
        with get_db_connection(db_config) as conn:
            while True:
                try:
                    msg = consumer.poll(1.0)
                    if msg is None:
                        continue

                    value = msg.value()
                    if value is None:
                        print("Mensaje recibido pero vacío o no deserializable.")
                        continue
                   
                    try:
                        handle_tle_message(conn, value)
                        logger.info("Mensaje procesado con éxito.")
                    except Exception as e:
                        logger.error(f"Error procesando mensaje: {e}", exc_info=True)

                except Exception as e:
                    logger.error(f"Error procesando mensaje: {e}", exc_info=True)
    except KeyboardInterrupt:
        logger.info("Interrupción manual detectada. Cerrando consumidor...")
    finally:
        consumer.close()
        logger.info("Consumidor cerrado correctamente.")