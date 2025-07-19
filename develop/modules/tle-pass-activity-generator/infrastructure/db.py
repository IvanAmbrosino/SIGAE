import psycopg2
from contextlib import contextmanager

@contextmanager
def get_db_connection(config):
    conn = psycopg2.connect(
        dbname=config['dbname'],
        user=config['user'],
        password=config['password'],
        host=config['host'],
        port=config.get('port', 5432)
    )
    try:
        yield conn
    finally:
        conn.close()
        