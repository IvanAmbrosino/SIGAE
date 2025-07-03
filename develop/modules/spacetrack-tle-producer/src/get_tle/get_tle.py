"""Busca el TLE de los satelites SAOCOM en el MOC"""
import json
import logging
import requests
from datetime import datetime, timezone
from config_manager import ConfigManager

class GetTleSpaceTrack:
    """Clase que obtiene TLEs de SpaceTrack"""
    #https://www.space-track.org/basicspacedata/query/class/tle_latest/ORDINAL/1/NORAD_CAT_ID/$lista/orderby/TLE_LINE1\ ASC/format/3le/

    def __init__(self, tmp_dir, logger : logging.Logger = None):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        self.space_track_config = self.config["space_track_config"]
        self.site_credentials = {
            'identity': self.space_track_config["username"],
            'password': self.config_manager.read_secret(self.space_track_config["password"])
        }
        self.list_satellites_str = None
        self.tmp_dir = tmp_dir
        self.logger = logger

    def make_json_data(self, response: dict) -> dict:
        """Convierte la respuesta de SpaceTrack a un diccionario"""
        data = {}
        for item in response:
            norad_cat_id = item["NORAD_CAT_ID"]
            if norad_cat_id not in data:
                dt = datetime.fromisoformat(item["EPOCH"]).replace(tzinfo=timezone.utc)
                timestamp_millis = int(dt.timestamp() * 1000)
                data[norad_cat_id] = {
                    "satellite_name": item["OBJECT_NAME"],
                    "line1": item["TLE_LINE1"],
                    "line2": item["TLE_LINE2"],
                    "timestamp": timestamp_millis
                }
        return data

    def get_tles(self, list_satellites: list[str]) -> dict | None:
        """Obtiene los TLEs de los satelites del listado"""
        self.list_satellites_str = ",".join(list_satellites)
        self.logger.info("Querry a SpaceTrack ejecutada: %s",
            self.space_track_config["uri_base"] +
            self.space_track_config["request_cmd_action"] +
            self.space_track_config["request_get_last"] +
            "/" + self.list_satellites_str +
            self.space_track_config["order"] +
            self.space_track_config["format"]
            )

        class MyError(Exception):
            """Clase de excepcion personalizada"""
            def __init___(self,args):
                Exception.__init__(self,f"my exception was raised with arguments {args}")
                self.args = args

        with requests.Session() as session:
            self.logger.debug("Login credentials: %s",self.site_credentials)
            resp = session.post(self.space_track_config["uri_base"] +
                                self.space_track_config["request_login"],
                                data = self.site_credentials)
            self.logger.debug("Login response: %s",resp.text)
            if resp.status_code != 200:
                self.logger.error("Login response: %s",resp.text)
                raise MyError(resp, "POST fail on login")

            resp = session.get(self.space_track_config["uri_base"] +
                               self.space_track_config["request_cmd_action"] +
                               self.space_track_config["request_get_last"] +
                               "/" + self.list_satellites_str +
                               self.space_track_config["order"] +
                               self.space_track_config["format"]
                               )
            if resp.status_code != 200:
                self.logger.error("Error en el request: %s",resp.text)
                raise MyError(resp, "GET fail on request")

            self.logger.info("GET request successful")
            session.close()
            return self.make_json_data(json.loads(resp.text))

        return None
