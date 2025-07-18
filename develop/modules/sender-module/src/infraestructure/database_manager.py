"""Adaptador de PostgreSQL"""
from datetime import datetime
from typing import List, Dict, Optional
import psycopg2

class DatabaseManager:
    """Clase adaptadora de PosgreSQL"""
    def __init__(self, dbname: str, user: str, password: str, host: str = 'localhost', port: int = 5432):
        """Inicializa la conexión a la base de datos"""
        self.conn_params = {
            'dbname': dbname,
            'user': user,
            'password': password,
            'host': host,
            'port': port
        }
        self.connection = None

    def connect(self):
        """Establece la conexión con la base de datos"""
        try:
            self.connection = psycopg2.connect(**self.conn_params)
            print("Conexión establecida correctamente")
        except psycopg2.Error as e:
            print(f"Error al conectar a PostgreSQL: {e}")

    def disconnect(self):
        """Cierra la conexión con la base de datos"""
        if self.connection:
            self.connection.close()
            print("Conexión cerrada")

    def execute_query(self, query: str, params: tuple = None, fetch: bool = False):
        """Ejecuta una consulta SQL y retorna los resultados si es necesario"""
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())

            if fetch:
                columns = [desc[0] for desc in cursor.description]
                results = cursor.fetchall()
                return [dict(zip(columns, row)) for row in results]

            self.connection.commit()
            return True

        except psycopg2.Error as e:
            self.connection.rollback()
            print(f"Error al ejecutar consulta: {e}")
            return False
        finally:
            if cursor:
                cursor.close()

    # Operaciones para la tabla satellites
    def get_satellite(self, satellite_id: str) -> Optional[Dict]:
        """Obtiene un satélite por su ID"""
        query = "SELECT * FROM satellites WHERE id = %s"
        results = self.execute_query(query, (satellite_id,), fetch=True)
        return results[0] if results else None

    def update_satellite_priority(self, satellite_id: str, new_priority: str) -> bool:
        """Actualiza el nivel de prioridad de un satélite"""
        query = """
        UPDATE satellites 
        SET priority_level = %s, updated_at = CURRENT_TIMESTAMP 
        WHERE id = %s
        """
        return self.execute_query(query, (new_priority, satellite_id))

    # Operaciones para la tabla antennas
    def get_antenna(self, antenna_id: str) -> Optional[Dict]:
        """Obtiene una antena por su ID"""
        query = "SELECT * FROM antennas WHERE id = %s"
        results = self.execute_query(query, (antenna_id,), fetch=True)
        return results[0] if results else None

    def get_active_antennas(self) -> List[Dict]:
        """Obtiene todas las antenas activas"""
        query = "SELECT * FROM antennas WHERE is_active = TRUE"
        return self.execute_query(query, fetch=True)

    # Operaciones para la tabla activities
    def get_activities_between_dates(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Obtiene actividades entre dos fechas"""
        query = """
        SELECT a.*, s.name as satellite_name 
        FROM activities a
        JOIN satellites s ON a.satellite_id = s.id
        WHERE a.start_time BETWEEN %s AND %s
        ORDER BY a.start_time
        """
        return self.execute_query(query, (start_date, end_date), fetch=True)

    def get_critical_activities(self) -> List[Dict]:
        """Obtiene actividades críticas"""
        query = """
        SELECT a.*, s.name as satellite_name 
        FROM activities a
        JOIN satellites s ON a.satellite_id = s.id
        WHERE a.priority = 'critical' AND a.status NOT IN ('completed', 'cancelled')
        ORDER BY a.start_time
        """
        return self.execute_query(query, fetch=True)

    def update_activity_status(self, activity_id: str, new_status: str) -> bool:
        """Actualiza el estado de una actividad"""
        query = """
        UPDATE activities 
        SET status = %s, updated_at = CURRENT_TIMESTAMP 
        WHERE id = %s
        """
        return self.execute_query(query, (new_status, activity_id))

    # Operaciones para la tabla activity_assignments
    def assign_activity_to_antenna(self, activity_id: str, antenna_id: str, assigned_by: str) -> bool:
        """Asigna una actividad a una antena"""
        query = """
        INSERT INTO activity_assignments 
        (id, activity_id, antenna_id, assigned_by) 
        VALUES (uuid_generate_v4(), %s, %s, %s)
        """
        return self.execute_query(query, (activity_id, antenna_id, assigned_by))

    def confirm_assignment(self, assignment_id: str, confirmed_by: str) -> bool:
        """Confirma una asignación de actividad"""
        query = """
        UPDATE activity_assignments 
        SET is_confirmed = TRUE, confirmed_by = %s, confirmed_at = CURRENT_TIMESTAMP 
        WHERE id = %s
        """
        return self.execute_query(query, (confirmed_by, assignment_id))

    # Operaciones para la tabla tle_data
    def get_latest_tle(self, satellite_id: str) -> Optional[Dict]:
        """Obtiene el TLE más reciente para un satélite"""
        query = """
        SELECT * FROM tle_data 
        WHERE satellite_id = %s AND is_valid = TRUE 
        ORDER BY epoch DESC 
        LIMIT 1
        """
        results = self.execute_query(query, (satellite_id,), fetch=True)
        return results[0] if results else None

    def add_tle_data(self, satellite_id: str, line1: str, line2: str, epoch: datetime, source: str) -> bool:
        """Añade nuevos datos TLE para un satélite"""
        query = """
        INSERT INTO tle_data 
        (id, satellite_id, line1, line2, epoch, source) 
        VALUES (uuid_generate_v4(), %s, %s, %s, %s, %s)
        """
        return self.execute_query(query, (satellite_id, line1, line2, epoch, source))
