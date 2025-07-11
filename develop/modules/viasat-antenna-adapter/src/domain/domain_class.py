"""Clases del dominio"""
from dataclasses import dataclass

@dataclass
class TLE:
    """Clase que representa un TLE (Two-Line Element)"""
    nombre_archivo: str
    contenido: str
    antena_id: str
    norad_id: str
    satellite_name: str
    fecha: str
    line1: str
    line2: str

@dataclass
class Planificacion:
    """Clase que representa una planificacion de antena"""
    tipo: str
    antena_id: str
    timestamp: str
    operaciones: list

@dataclass
class Actividades:
    """Clase que representa una actividad en la planificacion"""
    accion: str
    norad_id: str
    ventana_tiempo: dict
    metadata: dict


