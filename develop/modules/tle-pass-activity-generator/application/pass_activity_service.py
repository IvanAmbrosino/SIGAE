from skyfield.api import EarthSatellite, load, wgs84
from datetime import datetime, timedelta
from domain.tle_pass import PassActivity
from math import floor
import re

# Ejemplo de ubicación de estación
STATION_LAT = -34.6  # Buenos Aires
STATION_LON = -58.4
STATION_ELEV = 25  # metros


def get_norad_id(line1: str) -> str:
    # Usa regex para encontrar el patrón: "1 <id>U"
    match = re.match(r"1\s+(\d{5})U", line1)
    if match:
        return match.group(1)
    raise ValueError("Formato de TLE inválido")



def calcular_pasadas(tle_name, tle_line1, tle_line2, start_time, end_time):
    ts = load.timescale()
    satellite = EarthSatellite(tle_line1, tle_line2, tle_name, ts)
    station = wgs84.latlon(STATION_LAT, STATION_LON, STATION_ELEV)
    t0 = ts.utc(start_time)
    t1 = ts.utc(end_time)
    # Cada 30 segundos
    times, events = satellite.find_events(station, t0, t1, altitude_degrees=10.0)
    norad_id = get_norad_id(tle_line1)
    pasadas = []
    for i in range(0, len(events), 3):
        if i+2 < len(events):
            aos = times[i].utc_datetime()
            max_elev = times[i+1].utc_datetime()
            los = times[i+2].utc_datetime()
            duration = int((los - aos).total_seconds())

            # Calcular el número de órbita
            orbit_number = calcular_orbit_number(satellite, aos)
            print(f"Calculando órbita {orbit_number} para {tle_name} en AOS: {aos}, Max Elevación: {max_elev}, LOS: {los}")

            pasada = PassActivity(
                satellite_id=norad_id,
                orbit_number=orbit_number,
                start_time=aos,
                max_elevation_time=max_elev,
                end_time=los,
                duration=duration
            )
            pasadas.append(pasada)
    return pasadas

def calcular_orbit_number(satellite, time_dt):
    epoch = satellite.epoch.utc_datetime()
    mean_motion = satellite.model.no_kozai * 1440 / (2 * 3.141592653589793)
    delta_days = (time_dt - epoch).total_seconds() / 86400  # días fraccionales
    orbit_number_epoch = int(satellite.model.revnum)  # número de revoluciones en el epoch

    orbit_number_actual = orbit_number_epoch + mean_motion * delta_days
    return floor(orbit_number_actual)