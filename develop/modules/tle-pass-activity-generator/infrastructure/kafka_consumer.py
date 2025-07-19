
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import StringDeserializer
from confluent_kafka import DeserializingConsumer

from infrastructure.logger import setup_logger
from application.orchestrator import Orchestrator


def consume_tle_messages(config, orchestrator: Orchestrator):
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
    consumer.subscribe([config['kafka']['topic']])

    logger = setup_logger(__name__)
    logger.info("Esperando mensajes de TLE...")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue

            value = msg.value()
            if value is None:
                logger.warning("Mensaje recibido pero vacío o no deserializable.")
                continue

            try:
                orchestrator.handle_tle_message(value)
                logger.info("Mensaje procesado con éxito.")
            except Exception as e:
                logger.error(f"Error procesando mensaje: {e}", exc_info=True)

    except KeyboardInterrupt:
        logger.info("Interrupción manual detectada. Cerrando consumidor...")
    finally:
        consumer.close()
        logger.info("Consumidor cerrado correctamente.")