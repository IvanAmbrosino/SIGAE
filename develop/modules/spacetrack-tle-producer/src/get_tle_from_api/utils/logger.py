from asyncio.log import logger
import logging
from pathlib import Path

def load_logger(self) -> None:
        """Load logger configuration."""

        self.logs_config = {
        "folder":"logs",
        "filename": "test.log",
        "rotation": 5,
        "size": 5000000,
        "debug_mode": True
        }

        self.script_dir = Path(__file__).resolve().parent
        try:
            if not logger.handlers:
                log_level = logging.DEBUG if self.logs_config["debug_mode"] else logging.INFO
                logger.setLevel(log_level)
                handler = logging.handlers.RotatingFileHandler(
                    filename=(f'get_tle_from_api/{self.logs_config["folder"]}/{self.logs_config["filename"]}'),
                    mode='a', maxBytes=self.logs_config["size"],
                    backupCount= self.logs_config["rotation"],
                    encoding='utf-8')
                formatter = logging.Formatter(
                    "%(asctime) 15s - %(process)d - %(name)s -\
                        %(lineno)s - %(levelname)s - %(message)s")
                handler.setFormatter(formatter)
                logger.addHandler(handler)
        except TypeError as e:
            logger.error("error en la generacion de logs: %s",e)
        