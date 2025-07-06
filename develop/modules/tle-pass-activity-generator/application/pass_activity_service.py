from skyfield.api import EarthSatellite, load, wgs84
from datetime import datetime, timedelta
from domain.tle_pass import PassActivity

# Ejemplo de ubicación de estación
STATION_LAT = -34.6  # Buenos Aires
STATION_LON = -58.4
STATION_ELEV = 25  # metros

def calcular_pasadas(tle_name, tle_line1, tle_line2, start_time, end_time):
    ts = load.timescale()
    satellite = EarthSatellite(tle_line1, tle_line2, tle_name, ts)
    station = wgs84.latlon(STATION_LAT, STATION_LON, STATION_ELEV)
    t0 = ts.utc(start_time)
    t1 = ts.utc(end_time)
    # Cada 30 segundos
    times, events = satellite.find_events(station, t0, t1, altitude_degrees=10.0)
    pasadas = []
    for i in range(0, len(events), 3):
        if i+2 < len(events):
            aos = times[i].utc_datetime()
            max_elev = times[i+1].utc_datetime()
            los = times[i+2].utc_datetime()
            duration = int((los - aos).total_seconds())
            # Acaaa averiguar como calcular el número de órbita
            orbit_number = None

            pasada = PassActivity(
                satellite_id=tle_name,
                orbit_number=orbit_number,
                start_time=aos,
                max_elevation_time=max_elev,
                end_time=los,
                duration=duration
            )
            pasadas.append(pasada)
    return pasadas
