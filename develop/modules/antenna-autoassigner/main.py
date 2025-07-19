import yaml


from application.orchestrator import Orchestrator


def load_config():
    with open('configs/config.yaml', 'r') as f:
        return yaml.safe_load(f)
    
if __name__ == "__main__":
    #consume_tle_messages()
    config = load_config()
    db_config = config['database']

