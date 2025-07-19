from infrastructure.kafka_consumer import consume_tle_messages
import yaml

from infrastructure.repositories.tle_repository_postgres import PostgresTleRepository
from infrastructure.repositories.activity_repository_postgres import PostgresActivityRepository
from infrastructure.repositories.ground_station_repository_postgres import PostgresGroundStationRepository
from infrastructure.repositories.satellite_repository_postgres import PostgresSatelliteRepository


from application.orchestrator import Orchestrator


def load_config():
    with open('configs/config.yaml', 'r') as f:
        return yaml.safe_load(f)
    
if __name__ == "__main__":
    #consume_tle_messages()
    config = load_config()
    db_config = config['database']

    tle_repo = PostgresTleRepository(db_config)
    satellite_repo = PostgresSatelliteRepository(db_config)
    gs_repo = PostgresGroundStationRepository(db_config)
    pass_repo = PostgresActivityRepository(db_config)

    orchestrator = Orchestrator(
        tle_repository=tle_repo,
        satellite_repository=satellite_repo,
        ground_station_repository=gs_repo,
        pass_activity_repository=pass_repo
    )

    consume_tle_messages(config, orchestrator)
