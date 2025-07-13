
import yaml
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import StringDeserializer
from confluent_kafka import DeserializingConsumer
from application.pass_activity_service import compute_passes
from application.tle_service import process_and_save_tle

from datetime import datetime, timedelta, timezone
from infrastructure.db import get_db_connection, save_pass_activities

def load_config():
    with open('configs/config.yaml', 'r') as f:
        return yaml.safe_load(f)

def consume_tle_messages():
    config = load_config()

    db_config = {
        'dbname': 'planificacion_satelital',
        'user': 'planificador_app',
        'password': 'SecurePassword123!',
        'host': 'satplan_db',
        'port': 5432
    }
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

    print("Esperando mensajes de TLE...")
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
                    
                    process_and_save_tle(conn, value)

                    print(f"Recibido TLE: {value}")
                    tle_name = value.get('satellite_name')
                    tle_line1 = value.get('line1')
                    tle_line2 = value.get('line2')

                    start_time = datetime.now(timezone.utc)
                    end_time = start_time + timedelta(hours=24)

                    pasadas = compute_passes(tle_name, tle_line1, tle_line2, start_time, end_time)

                    save_pass_activities(conn, pasadas)

                    for pasada in pasadas:
                        print(
                            f"Pasada calculada y guardada: Satélite {pasada.satellite_id} "
                            f"(órbita {pasada.orbit_number}) - Inicio: {pasada.start_time}, "
                            f"Máx. elevación: {pasada.max_elevation_time}, Fin: {pasada.end_time}, "
                            f"Duración: {pasada.duration}s, Prioridad: {pasada.priority.value}, Estado: {pasada.status.value}"
                        )

                except Exception as e:
                    print(f"[ERROR] Procesando mensaje: {e}")
    except KeyboardInterrupt:
        print("Interrupción manual detectada. Cerrando consumidor...")
    finally:
        consumer.close()

if __name__ == "__main__":
    consume_tle_messages()
