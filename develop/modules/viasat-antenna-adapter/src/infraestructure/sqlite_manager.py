"""SQLite Manager for cache and planning data."""
import sqlite3
from datetime import datetime, timedelta, timezone

# -----------------------------------------------
# CONFIGURACIÓN
# -----------------------------------------------
PLANNING_DB = "/app/db/planning_cache.db"
TLE_DB = "/app/db/tle_cache.db"

# -----------------------------------------------
# CREACIÓN DE LAS BASES
# -----------------------------------------------
class SQLiteManager:
    """Database Manager"""
    def init_planning_db(self) -> None:
        """Initializes the planning database."""
        conn = sqlite3.connect(PLANNING_DB)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS planificaciones (
                task_id TEXT PRIMARY KEY,
                antenna_id TEXT,
                satellite TEXT,
                norad_id TEXT,
                config_id INTEGER,
                start_time TEXT,
                end_time TEXT,
                created_at TEXT
            )
        """)
        conn.commit()
        conn.close()

    def init_tle_db(self) -> None:
        """Initializes the TLE database."""
        conn = sqlite3.connect(TLE_DB)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS tles (
                norad_id TEXT PRIMARY KEY,
                name TEXT,
                line1 TEXT,
                line2 TEXT,
                timestamp TEXT,
                updated_at TEXT
            )
        """)
        conn.commit()
        conn.close()

    # -----------------------------------------------
    # INSERCIÓN / ACTUALIZACIÓN
    # -----------------------------------------------

    def upsert_planificacion(self, pase) -> None:
        """Inserts or updates a planning entry in the database."""
        conn = sqlite3.connect(PLANNING_DB)
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO planificaciones (
                task_id, antenna_id, satellite, norad_id, config_id,
                start_time, end_time, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pase["task_id"],
            pase["antenna_id"],
            pase["satellite"],
            pase["norad_id"],
            pase["config_id"],
            self.to_iso_z(pase["start"]),
            self.to_iso_z(pase["end"]),
            datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        ))
        conn.commit()
        conn.close()

    def upsert_tle(self, tle) -> None:
        """Inserts or updates a TLE entry in the database."""
        conn = sqlite3.connect(TLE_DB)
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO tles (
                norad_id, name, line1, line2, timestamp, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            tle["norad_id"], tle["satellite_name"],
            tle["line1"], tle["line2"],
            self.to_iso_z(tle["timestamp"]),
            datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        ))
        conn.commit()
        conn.close()

    # -----------------------------------------------
    # DELETE / PURGE
    # -----------------------------------------------

    def delete_activity_by_id(self, task_id: str) -> None:
        """Delete activity by ID"""
        conn = sqlite3.connect(TLE_DB)
        c = conn.cursor()
        c.execute(f"DELETE tles WHERE task_id = {task_id}")
        conn.commit()
        conn.close()

    def purge_activities(self) -> None:
        """Delete all activities"""
        conn = sqlite3.connect(TLE_DB)
        c = conn.cursor()
        c.execute("DELETE tles")
        conn.commit()
        conn.close()

    # -----------------------------------------------
    # CONSULTAS
    # -----------------------------------------------

    def get_freshness_tle(self, norad_id, freshness_hours=48) -> dict:
        """Obtains the TLE for a given NORAD ID, checking freshness."""
        conn = sqlite3.connect(TLE_DB)
        c = conn.cursor()
        limit = (
            datetime.utcnow() - timedelta(hours=freshness_hours)
                 ).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        c.execute("""
            SELECT line1, line2 FROM tles
            WHERE norad_id = ? AND timestamp > ? 
            ORDER BY updated_at DESC LIMIT 1
        """, (norad_id, limit))
        row = c.fetchone()
        conn.close()
        if row:
            return {"line1": row[0], "line2": row[1]}
        print(f"No TLE found for NORAD ID {norad_id} or it is too old.")
        return None

    def get_last_tle(self, norad_id) -> list:
        """Obtains last TLE order by timestamp."""
        conn = sqlite3.connect(TLE_DB)
        c = conn.cursor()
        c.execute("""
            SELECT line1, line2 FROM tles
            WHERE norad_id = ?
            ORDER BY timestamp DESC
            LIMIT 1;
        """, (norad_id,))
        row = c.fetchone()
        conn.close()
        return row

    def pase_ya_programado(self, task_id) -> bool:
        """Checks if a task is already scheduled in the planning database."""
        conn = sqlite3.connect(PLANNING_DB)
        c = conn.cursor()
        c.execute("SELECT 1 FROM planificaciones WHERE task_id = ?", (task_id,))
        exists = c.fetchone() is not None
        conn.close()
        return exists

    def exist_passes_in_window(self,init_time: datetime,end_time: datetime) -> bool:
        """Returns true if there are activities in a specified window"""
        conn = sqlite3.connect(PLANNING_DB)
        c = conn.cursor()
        # where_1 = f"start_time <= {init_time} and end_time > {init_time}" # Empieza antes y termina despues del init
        # where_2 = f"start_time < {end_time} and  end_time < {end_time}"   # Empieza antes y termina despues del end
        # where_3 = f"start_time >= {init_time} and end_time <= {end_time}" # La actividad vieja se encuentra completamente adentro de la nueva
        # where_4 = f"start_time <= {init_time} and end_time >= {end_time}" # La actividad nueva esta adentro de otra actividad vieja

        where = """
        (start_time <= ? AND end_time > ?) OR
        (start_time < ? AND end_time >= ?) OR
        (start_time >= ? AND end_time <= ?) OR
        (start_time <= ? AND end_time >= ?)
    """

        params = (
            init_time, init_time,
            end_time, end_time,
            init_time, end_time,
            init_time, end_time,
        )

        c.execute(f"SELECT norad_id FROM planificaciones WHERE {where}", params)
        exists = c.fetchone() is not None
        conn.close()
        return exists

    def get_satellites_planificados(self) -> list:
        """
        Gets the list of satellites planned for the unit
        Returns a list of satellites without repeating itself
        """
        list_satellites = []
        now =  datetime.utcnow().isoformat().split('.')[0]+'Z'
        conn = sqlite3.connect(PLANNING_DB)
        c = conn.cursor()
        c.execute("SELECT norad_id FROM planificaciones  WHERE start_time > ?", (now,))
        rows = c.fetchall()
        for row in rows: # Eliminamos los elementos repetidos
            if row not in list_satellites:
                list_satellites.append(row)
        conn.close()
        return list_satellites

    # ------------------------------------------------
    # LIMPIEZA DE ENTRADAS ANTIGUAS - GARBAJE COLECTOR
    # ------------------------------------------------

    def limpiar_tle(self, dias: int = 3) -> None:
        """Cleans up old TLE entries older than a specified number of days."""
        limite = (datetime.utcnow() - timedelta(days=dias)).isoformat().split('.')[0]+'Z'
        conn = sqlite3.connect(TLE_DB)
        c = conn.cursor()
        c.execute("DELETE FROM tles WHERE timestamp < ?", (limite,))
        conn.commit()
        conn.close()

    def limpiar_planificaciones(self, dias: int = 1) -> None:
        """Cleans up old planning entries older than a specified number of days."""
        limite = (datetime.utcnow() - timedelta(days=dias)).isoformat().split('.')[0]+'Z'
        conn = sqlite3.connect(PLANNING_DB)
        c = conn.cursor()
        c.execute("DELETE FROM planificaciones WHERE end_time < ?", (limite,))
        conn.commit()
        conn.close()

    # -----------------------------------------------
    # INIT de ambas bases
    # -----------------------------------------------
    def inicializar(self) -> None:
        """Initializes both databases if they do not exist."""
        self.init_planning_db()
        self.init_tle_db()

    # -----------------------------------------------
    # Funciones utiles
    # -----------------------------------------------
    def to_iso_z(self, s: str) -> str:
        """Convierte fecha en texto o datetime a formato ISO con 'Z'"""
        if isinstance(s, str):
            s = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return s.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
