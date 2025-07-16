from get_tle import GetTleSpaceTrack

def obtener_tles(satelites, logger): #de la API de SpaceTrack
        tle_getter = GetTleSpaceTrack('tmp', logger)
        norad_ids = [str(s["id"]) for s in satelites]
        
        if not norad_ids:
            return {}

        print(f"Consultando TLEs para los satélites: {norad_ids}")
        # tles = tle_getter.get_tles(norad_ids) 
        tles = {'25544': {'satellite_name': 'ISS (ZARYA)', 'line1': '1 25544U 98067A   25194.43411487  .00010152  00000-0  18227-3 0  9995', 'line2': '2 25544  51.6340 176.9702 0002675   6.8375 353.2650 15.50520436519237', 'timestamp': 1752402307000}, '27424': {'satellite_name': 'AQUA', 'line1': '1 27424U 02022A   25194.64751222  .00000601  00000-0  13142-3 0  9996', 'line2': '2 27424  98.3791 153.3336 0001148  53.8590  61.5800 14.61343650233816', 'timestamp': 1752420745000}}
        return tles