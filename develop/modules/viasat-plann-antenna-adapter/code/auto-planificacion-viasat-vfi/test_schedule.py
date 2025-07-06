from schedule_acu4100 import ViasatScheduleVFI as VFI
from cgssdbops import cgss_db_ops
from datetime import datetime
from json import dumps
from unittest import TestCase
import pytest

INIT_TIME = datetime(2024, 2, 17, 12, 44, 0)
END_TIME = datetime(2024, 2, 19, 12, 45, 0)

TEST_PLAN = []

VFI = VFI()
@pytest.mark.parametrize("bbdd, plan, expected_result", [
    ({"bbdd":{"host":"10.0.3.15","user":"sa","passwd":""}},
     {"Plan": {"db": "L-HPI-DB-S","table": "Planificaciones"}},list)])

def test_get_activities4unit(bbdd, plan, expected_result):
    """Test get activities"""
    conn, cur = cgss_db_ops.open_db_conn(bbdd["bbdd"]["host"], bbdd["bbdd"]["user"],
                                         bbdd["bbdd"]["passwd"], plan["Plan"]["db"])
    activities = cgss_db_ops.query_plan(cur, VFI.return_formatted_time(
        (datetime.utcnow()-INIT_TIME).total_seconds()/60),
        VFI.return_formatted_time((datetime.utcnow()-END_TIME).total_seconds()/60),
        plan["Plan"]["db"], plan["Plan"]["table"])
    isinstance(activities,expected_result)
    cgss_db_ops.close_db_conn(conn)

@pytest.mark.parametrize("schedule, expected_result", [(
    {"0": {"Satelite": "SAOCOM-1B", "Orbita": "18782", "FechaHoraInicial": "2024-02-19T20:47:09.200000", "FechaHoraFinal": "2024-02-19T20:58:27.200000", "idMacro": 1730, "Estado": "A"}, 
    "1": {"Satelite": "SAOCOM-1A", "Orbita": "29045", "FechaHoraInicial": "2024-02-19T21:37:51.200000", "FechaHoraFinal": "2024-02-19T21:50:57.200000", "idMacro": 1727, "Estado": "A"}, 
    "2": {"Satelite": "SAOCOM-1B", "Orbita": "18783", "FechaHoraInicial": "2024-02-19T22:22:24.800000", "FechaHoraFinal": "2024-02-19T22:35:00.800000", "idMacro": 1730, "Estado": "A"}, 
    "3": {"Satelite": "SAOCOM-1A", "Orbita": "29046", "FechaHoraInicial": "2024-02-19T23:16:14.100000", "FechaHoraFinal": "2024-02-19T23:25:26.100000", "idMacro": 1727, "Estado": "A"}, 
    "4": {"Satelite": "SAOCOM-1A", "Orbita": "29052", "FechaHoraInicial": "2024-02-20T09:30:56.200000", "FechaHoraFinal": "2024-02-20T09:42:26.200000", "idMacro": 1727, "Estado": "A"}, 
    "5": {"Satelite": "SAOCOM-1B", "Orbita": "18790", "FechaHoraInicial": "2024-02-20T10:14:34.800000", "FechaHoraFinal": "2024-02-20T10:27:40.800000", "idMacro": 1730, "Estado": "A"}, 
    "6": {"Satelite": "SAOCOM-1A", "Orbita": "29053", "FechaHoraInicial": "2024-02-20T11:06:37.400000", "FechaHoraFinal": "2024-02-20T11:19:01.400000", "idMacro": 1727, "Estado": "A"}, 
    "7": {"Satelite": "SAOCOM-1B", "Orbita": "18791", "FechaHoraInicial": "2024-02-20T11:52:03.100000", "FechaHoraFinal": "2024-02-20T12:01:21.100000", "idMacro": 1730, "Estado": "A"}, 
    "8": {"Satelite": "SAOCOM-1B", "Orbita": "18797", "FechaHoraInicial": "2024-02-20T21:04:34.200000", "FechaHoraFinal": "2024-02-20T21:16:52.200000", "idMacro": 1730, "Estado": "A"}, 
    "9": {"Satelite": "SAOCOM-1A", "Orbita": "29060", "FechaHoraInicial": "2024-02-20T21:55:49.300000", "FechaHoraFinal": "2024-02-20T22:08:55.300000", "idMacro": 1727, "Estado": "A"}, 
    "10": {"Satelite": "SAOCOM-1B", "Orbita": "18798", "FechaHoraInicial": "2024-02-20T22:40:54.900000", "FechaHoraFinal": "2024-02-20T22:52:42.900000", "idMacro": 1730, "Estado": "A"}, 
    "11": {"Satelite": "SAOCOM-1B", "Orbita": "18804", "FechaHoraInicial": "2024-02-21T08:58:19.200000", "FechaHoraFinal": "2024-02-21T09:06:55.200000", "idMacro": 1730, "Estado": "A"}, 
    "12": {"Satelite": "SAOCOM-1A", "Orbita": "29067", "FechaHoraInicial": "2024-02-21T09:48:35.800000", "FechaHoraFinal": "2024-02-21T10:00:59.800000", "idMacro": 1727, "Estado": "A"}, 
    "13": {"Satelite": "SAOCOM-1B", "Orbita": "18805", "FechaHoraInicial": "2024-02-21T10:32:35.100000", "FechaHoraFinal": "2024-02-21T10:45:41.100000", "idMacro": 1730, "Estado": "A"}, 
    "14": {"Satelite": "SAOCOM-1A", "Orbita": "29068", "FechaHoraInicial": "2024-02-21T11:24:56.500000", "FechaHoraFinal": "2024-02-21T11:36:32.500000", "idMacro": 1727, "Estado": "A"}}, True)]
)

def test_plan_created(schedule, expected_result):
    """Test plan"""
    bbdd = {"bbdd":{"host":"10.0.3.15","user":"sa","passwd":""}},
    plan = {"Plan": {"db": "L-HPI-DB-S","table": "Planificaciones"}}
    conn, cur = cgss_db_ops.open_db_conn(bbdd["bbdd"]["host"], bbdd["bbdd"]["user"],
                                         bbdd["bbdd"]["passwd"], plan["Plan"]["db"])
    activities = cgss_db_ops.query_plan(cur, VFI.return_formatted_time(
        (datetime.utcnow()-INIT_TIME).total_seconds()/60),
        VFI.return_formatted_time((datetime.utcnow()-END_TIME).total_seconds()/60),
        plan["Plan"]["db"], plan["Plan"]["table"])
    print(len(activities))
    print(len(plan))
    TestCase().assertDictEqual(activities, plan)
    # assert activities == plan
    cgss_db_ops.close_db_conn(conn)

