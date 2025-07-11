"""SQLite Manager for cache and planning data."""
import sqlite3
from datetime import datetime, timedelta

# -----------------------------------------------
# CONFIGURACIÓN
# -----------------------------------------------
PLANNING_DB = "planning_cache.db"
TLE_DB = "tle_cache.db"

# -----------------------------------------------
# CREACIÓN DE LAS BASES
# -----------------------------------------------

def init_planning_db():
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

def init_tle_db():
    """Initializes the TLE database."""
    conn = sqlite3.connect(TLE_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS tles (
            norad_id TEXT PRIMARY KEY,
            line1 TEXT,
            line2 TEXT,
            tle_timestamp TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()

# -----------------------------------------------
# INSERCIÓN / ACTUALIZACIÓN
# -----------------------------------------------

def upsert_planificacion(pase):
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
        pase["start_time"],
        pase["end_time"],
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()

def upsert_tle(tle):
    """Inserts or updates a TLE entry in the database."""
    conn = sqlite3.connect(TLE_DB)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO tles (
            norad_id, line1, line2, tle_timestamp, updated_at
        ) VALUES (?, ?, ?, ?, ?)
    """, (
        tle["norad_id"], tle["line1"], tle["line2"],
        tle["tle_timestamp"], datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()

# -----------------------------------------------
# CONSULTAS
# -----------------------------------------------

def get_tle(norad_id, freshness_hours=48):
    """Obtains the TLE for a given NORAD ID, checking freshness."""
    conn = sqlite3.connect(TLE_DB)
    c = conn.cursor()
    limit = (datetime.utcnow() - timedelta(hours=freshness_hours)).isoformat()
    c.execute("""
        SELECT line1, line2 FROM tles
        WHERE norad_id = ? AND tle_timestamp > ? ORDER BY updated_at DESC LIMIT 1
    """, (norad_id, limit))
    row = c.fetchone()
    conn.close()
    if row:
        return {"line1": row[0], "line2": row[1]}
    else:
        print(f"No TLE found for NORAD ID {norad_id} or it is too old.")
    return None

def pase_ya_programado(task_id):
    """Checks if a task is already scheduled in the planning database."""
    conn = sqlite3.connect(PLANNING_DB)
    c = conn.cursor()
    c.execute("SELECT 1 FROM planificaciones WHERE task_id = ?", (task_id,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

# ------------------------------------------------
# LIMPIEZA DE ENTRADAS ANTIGUAS - GARBAJE COLECTOR
# ------------------------------------------------

def limpiar_tle(dias=3):
    """Cleans up old TLE entries older than a specified number of days."""
    limite = (datetime.utcnow() - timedelta(days=dias)).isoformat()
    conn = sqlite3.connect(TLE_DB)
    c = conn.cursor()
    c.execute("DELETE FROM tles WHERE tle_timestamp < ?", (limite,))
    conn.commit()
    conn.close()

def limpiar_planificaciones(dias=1):
    """Cleans up old planning entries older than a specified number of days."""
    limite = (datetime.utcnow() - timedelta(days=dias)).isoformat()
    conn = sqlite3.connect(PLANNING_DB)
    c = conn.cursor()
    c.execute("DELETE FROM planificaciones WHERE end_time < ?", (limite,))
    conn.commit()
    conn.close()

# -----------------------------------------------
# INIT de ambas bases
# -----------------------------------------------
def inicializar():
    """Initializes both databases if they do not exist."""
    init_planning_db()
    init_tle_db()
