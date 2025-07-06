#!/usr/bin/python3
from datetime import datetime,timedelta
import pytest
from make_vfi import make_vfi_sched
from make_vfi.xml_ops import OpsOverXML as XML
import pymssql
HOST = "10.0.3.14"
USER = "sa"
PASSWD = ""
BBDD = "L-HPI-DB-S"
TABLE = "Planificaciones"
logger = "Schedule ACU4100"

init_time = (datetime.utcnow()-timedelta(hours=0.5)).strftime(
    "%Y-%m-%dT%H:%M:%S")
end_time = (datetime.utcnow()+timedelta(hours=7)).strftime(
    "%Y-%m-%dT%H:%M:%S")

root = XML().create_root()
# List of conf to test
@pytest.mark.parametrize("activities", "unit", "action", "filename", "path",
                         [({0: {'Satelite': 'SPOT 6', 'Orbita': '47',
                                'FechaHoraInicial':'2024-03-14T13:45:38',
                                'FechaHoraFinal': '2024-03-14T13:59:40',
                             'idMacro': 1721, 'Estado': 'A'},
                            1: {'Satelite': 'SAOCOM-1A', 'Orbita': '29400',
                                'FechaHoraInicial': '2024-03-14T20:50:48.500000',
                                'FechaHoraFinal': '2024-03-14T21:02:06.500000',
                                'idMacro': 1698, 'Estado': 'A'},
                            2: {'Satelite': 'SAOCOM-1B', 'Orbita': '19138',
                                'FechaHoraInicial': '2024-03-14T21:33:59.300000',
                                'FechaHoraFinal': '2024-03-14T21:47:05.300000',
                                'idMacro': 1700, 'Estado': 'A'},
                            3: {'Satelite': 'SAOCOM-1A', 'Orbita': '29401',
                                'FechaHoraInicial': '2024-03-14T22:26:04.100000',
                                'FechaHoraFinal': '2024-03-14T22:38:40.100000',
                                'idMacro': 1698, 'Estado': 'A'}}),("ANTVSTF01"),
                          "ADD", ("text.xml"), (".")]
                         )
class TestClass:
    def add_passes(activities, unit, filename, path):
        assert make_vfi_sched(activities, unit, filename, path) == True
