"""Funcion Test que produce mensajes"""
import json
from datetime import datetime
from time import sleep
from confluent_kafka import Producer
from kafka.admin import KafkaAdminClient, NewTopic
class GeneradorTle():
    """Clase generadora de tles"""
    producer = None
    admin_client = None

    def conect_kafka_producer(self):
        """Conexion con kafka"""
        conf = {
        'bootstrap.servers': 'localhost:19092,localhost:29092,localhost:39092',  # Brokers de Kafka
        'client.id': 'python-producer'
        }
        self.admin_client = KafkaAdminClient(
            bootstrap_servers='localhost:19092,localhost:29092,localhost:39092'
        )

        self.producer = Producer(conf)

    def kafka_producer(self, topic, message):
        """Funcion que productora de mensajes"""
        topic_config = NewTopic(
            name=topic,
            num_partitions = 3,
            replication_factor = 3
        )
        print(message['line1'].split()[3].split(".")[0], message['timestamp'])
        existing_topics = self.admin_client.list_topics()
        if topic not in existing_topics:
            self.admin_client.create_topics(new_topics=[topic_config], validate_only=False)

        def delivery_report(err, msg):
            if err is not None:
                print(f'Message delivery failed: {err}')
            else:
                print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

        self.producer.produce(topic, value= json.dumps(message), callback=delivery_report)
        self.producer.flush()

if __name__ == "__main__":
    # Genera datos para los consumidores
    gtle = GeneradorTle()
    norad_ids, tles = [], []
    tles_2 = []
    tles_3 = []
    import random
    random.randint(0,9)
    with open('/home/iambrosino/actualiza_tle/viasat-tle-sender/src/configs/list_satellites.config', 'r',encoding='utf-8') as file:
        lines = file.readlines()
        for line in lines:
            norad_ids.append(line.split(';')[0].strip())
            tles.append({
                "name": f"{line.split(';')[1].strip()}",
                "line1": f"1 43641U 18076A   2430{random.randint(0,9)}.89974537 0.00000111  00000-0 014188-4 0    04",
                "line2": "2 43641  97.8887 109.4672 0001393  83.8212 141.0691 14.82130712    07",
                "timestamp": f"{datetime.now()}"
            })
            tles_2.append({
                "name": f"{line.split(';')[1].strip()}",
                "line1": "1 43641U 18076A   24294.89974537 0.00000111  00000-0 014188-4 0    04",
                "line2": "2 43641  97.8887 109.4672 0001393  83.8212 141.0691 14.82130712    07",
                "timestamp": f"{datetime.now()}"
            })
            tles_3.append({
                "name": f"{line.split(';')[1].strip()}",
                "line1": "1 43641U 18076A   24294.89974537 0.00000111  00000-0 014188-4 0    04",
                "line2": "2 43641  97.8887 109.4672 0001393  83.8212 141.0691 14.82130712    07",
                "timestamp": f"{datetime.now()}"
            })
    gtle.conect_kafka_producer()
    i = 0
    for norad_id in norad_ids:
        gtle.kafka_producer('TLE', tles[i])
        break
        # sleep(10)
        #gtle.kafka_producer(norad_id, tles_2[i])
        #gtle.kafka_producer(norad_id, tles_3[i])
        i += 1
