from skyfield.api import EarthSatellite, load, wgs84
from math import floor
from domain.entities.pass_activity import PassActivity
from domain.entities.tle_data import TleData
from typing import List

from domain.ports.ground_station_repository import GroundStationRepository


def compute_passes(
    tle: TleData,
    start_time,
    end_time,
    ground_station_repository: GroundStationRepository,
    min_elevation: float = 0.0,
) -> List[PassActivity]:

    ts = load.timescale()
    satellite = EarthSatellite(tle.line1, tle.line2, tle.satellite_id, ts)
    
    lat, lon, elev = ground_station_repository.get_station_coordinates()
    station = wgs84.latlon(lat, lon, elev)

    t0 = ts.utc(start_time)
    t1 = ts.utc(end_time)

    times, events = satellite.find_events(station, t0, t1, altitude_degrees=min_elevation)
    pasadas = []

    for i in range(0, len(events), 3):
        if i + 2 < len(events):
            aos = times[i].utc_datetime()
            max_elev_time = times[i + 1]
            los = times[i + 2].utc_datetime()
            duration = int((los - aos).total_seconds())

            difference = satellite - station
            topocentric = difference.at(max_elev_time)
            alt, _, _ = topocentric.altaz()
            max_elevation_deg = alt.degrees

            if max_elevation_deg < min_elevation:
                continue

            orbit_number = compute_orbit_number(satellite, aos)

            pasadas.append(PassActivity(
                satellite_id=str(tle.satellite_id),
                orbit_number=str(orbit_number),
                start_time=aos,
                max_elevation_time=max_elev_time.utc_datetime(),
                end_time=los,
                duration=duration,
                max_elevation=max_elevation_deg
            ))

    return pasadas


def compute_orbit_number(satellite, time_dt):
    epoch = satellite.epoch.utc_datetime()
    mean_motion = satellite.model.no_kozai * 1440 / (2 * 3.141592653589793)
    delta_days = (time_dt - epoch).total_seconds() / 86400
    orbit_number_epoch = int(satellite.model.revnum)
    return floor(orbit_number_epoch + mean_motion * delta_days)
