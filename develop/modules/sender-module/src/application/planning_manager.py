"""Modulo encargado de obtener el listado de planificacion para enviar"""
from datetime import datetime, timedelta
from infraestructure.config_manager import ConfigManager
from infraestructure.database_manager import DatabaseManager

class PlanningManager():
    """Clase principal para la obtencion de la planificacion y validacion de la misma"""
    def __init__(self):
        self.config_manager = ConfigManager()
        self.configs = self.config_manager.load_config()
        self.db_configs = self.configs['database']
        self.database_manager = DatabaseManager(
            dbname=     self.db_configs["dbname"],
            user=       self.db_configs["user"],
            password=   self.config_manager.read_secret(self.db_configs["password"]),
            host=       self.db_configs["host"]
        )

    def test_querrys(self):
        """Funcion de prueba de las funciones de consulta en la BD"""
        try:
            self.database_manager.connect()

            # Ejemplo 1: Consultar actividades entre fechas
            print("\nEjemplo 1: Consultar actividades entre fechas")
            start_date = datetime.now()
            end_date = start_date + timedelta(days=7)
            activities = self.database_manager.get_activities_between_dates(start_date, end_date)

            print(f"Actividades entre {start_date} y {end_date}:")
            for activity in activities[:3]:  # Mostrar solo las primeras 3 por brevedad
                print(f"{activity['satellite_name']} - {activity['start_time']} a {activity['end_time']} - Estado: {activity['status']}")

            # Ejemplo 2: Actualizar estado de una actividad
            print("\nEjemplo 2: Actualizar estado de actividad")
            if activities:
                activity_id = activities[0]['id']
                if self.database_manager.update_activity_status(activity_id, 'planned'):
                    print(f"Estado de actividad {activity_id} actualizado a 'planned'")

            # Ejemplo 3: Asignar actividad a antena
            print("\nEjemplo 3: Asignar actividad a antena")
            antennas = self.database_manager.get_active_antennas()
            if activities and antennas:
                activity_id = activities[0]['id']
                antenna_id = antennas[0]['id']
                if self.database_manager.assign_activity_to_antenna(activity_id, antenna_id, 'user-123'):
                    print(f"Actividad {activity_id} asignada a antena {antenna_id}")

            # Ejemplo 4: Obtener TLE más reciente para un satélite
            print("\nEjemplo 4: Obtener TLE de satélite")
            satellite_id = "sat-123"  # Cambiar por ID real
            tle_data = self.database_manager.get_latest_tle(satellite_id)
            if tle_data:
                print(f"TLE más reciente para satélite {satellite_id}:")
                print(f"Línea 1: {tle_data['line1']}")
                print(f"Línea 2: {tle_data['line2']}")
                print(f"Época: {tle_data['epoch']}")

        finally:
            self.database_manager.disconnect()

if __name__ == "__main__":
    PlanningManager().test_querrys()
