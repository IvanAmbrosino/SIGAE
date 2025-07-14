from skyfield.api import EarthSatellite, load, wgs84, EarthSatellite
from math import floor
from domain.tle_pass import TleData, PassActivity
import re
from typing import List
from typing import List
from infrastructure.db import get_station_coordinates


def get_norad_id(line1: str) -> str:
    # Usa regex para encontrar el patrón: "1 <id>U"
    match = re.match(r"1\s+(\d{5})U", line1)
    if match:
        return match.group(1)
    raise ValueError("Formato de TLE inválido")




def compute_passes(conn, tle: TleData, start_time, end_time, min_elevation: float = 0.0) -> List[PassActivity]:
    ts = load.timescale()
    satellite = EarthSatellite(tle.line1, tle.line2, tle.satellite_id, ts)
    
    lat, lon, elev = get_station_coordinates(conn)
    station = wgs84.latlon(lat, lon, elev)

    t0 = ts.utc(start_time)
    t1 = ts.utc(end_time)

    # Aquí usamos min_elevation para el filtro en find_events
    times, events = satellite.find_events(station, t0, t1, altitude_degrees=min_elevation)
    pasadas = []

    for i in range(0, len(events), 3):
        if i + 2 < len(events):
            aos = times[i].utc_datetime()
            max_elev_time = times[i + 1]
            los = times[i + 2].utc_datetime()
            duration = int((los - aos).total_seconds())

            # Calculamos elevación máxima real (en grados) en el tiempo de máxima elevación
            difference = satellite - station
            topocentric = difference.at(max_elev_time)
            alt, az, distance = topocentric.altaz()

            max_elevation_deg = alt.degrees

            # Filtrar pasadas que no alcancen la elevación mínima requerida
            if max_elevation_deg < min_elevation:
                continue

            orbit_number = compute_orbit_number(satellite, aos)

            pasada = PassActivity(
                satellite_id=tle.satellite_id,
                orbit_number=orbit_number,
                start_time=aos,
                max_elevation_time=max_elev_time.utc_datetime(),
                end_time=los,
                duration=duration,
                max_elevation=max_elevation_deg
            )
            pasadas.append(pasada)

    return pasadas


def compute_orbit_number(satellite, time_dt):
    epoch = satellite.epoch.utc_datetime()
    mean_motion = satellite.model.no_kozai * 1440 / (2 * 3.141592653589793)
    delta_days = (time_dt - epoch).total_seconds() / 86400  # días fraccionales
    orbit_number_epoch = int(satellite.model.revnum)  # número de revoluciones en el epoch

    orbit_number_actual = orbit_number_epoch + mean_motion * delta_days
    return floor(orbit_number_actual)