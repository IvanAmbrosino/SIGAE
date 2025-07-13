"""Module responsible for managing mounted configurations and environment variables"""
import os
import yaml
from pathlib import Path

DEFAULT_CONFIG_PATH = Path(__file__).parent / "/app/config/default_config.yaml"
MOUNTED_CONFIG_PATH = Path("/app/config/config.yaml")

# Mapeo ENV -> Claves en el dict final
ENV_TO_CONFIG_KEYS = {
    "ANTENNA_ID": ("app", "antenna_id"),
    "BROADCAST_TLE": ("app", "broadcast_tle"),
    "TLE_CACHE_DAYS": ("app", "tle_cache_days"),
    "LOG_LEVEL": ("app", "log_level")
}

class ConfigManager:
    """Configuration and Environment Variables Manager"""

    def load_yaml(self, path: str) -> dict:
        """Reads a YML file passed as a parameter and return dict"""
        with open(path, "r",encoding='utf-8') as f:
            return yaml.safe_load(f)

    def deep_merge(self, base: dict, override: dict) -> dict:
        """
        Performs a deep (recursive) merge of two dictionaries:
            - base: default config.
            - override: mounted config.
        """
        for key, value in override.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self.deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    def apply_env_vars(self, config):
        """Overwrites the configuration with environment variables"""
        for env_var, keys in ENV_TO_CONFIG_KEYS.items():
            if env_var in os.environ:
                val = os.environ[env_var]
                if val.lower() in ["true", "false"]:
                    val = val.lower() == "true"
                elif val.isdigit():
                    val = int(val)
                # Setear valor en la config
                d = config
                for k in keys[:-1]:
                    d = d.setdefault(k, {})
                d[keys[-1]] = val
        return config

    def load_config(self):
        """Function that loads all settings"""
        # Paso 1: Cargar default
        config = self.load_yaml(DEFAULT_CONFIG_PATH)

        # Paso 2: Si existe config montado, mergearlo
        if MOUNTED_CONFIG_PATH.exists():
            override = self.load_yaml(MOUNTED_CONFIG_PATH)
            config = self.deep_merge(config, override)

        # Paso 3: Override con variables de entorno
        config = self.apply_env_vars(config)

        return config
