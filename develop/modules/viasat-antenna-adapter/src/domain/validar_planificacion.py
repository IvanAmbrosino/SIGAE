"""Module that validates the different types of messages"""
import re
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from infraestructure.sqlite_manager import SQLiteManager # pylint: disable=import-error

class Validator(ABC):
    """Abstract class to define the validation strategy"""

    @abstractmethod
    def validate(self, menssage: dict) -> bool:
        """Obtiene un archivo al servidor SFTP"""

class ValidateTLE(Validator):
    """Class to validate TLE messages"""
    def __init__(self, logger: logging):
        self.logger = logger
        self.sqlite_manager = SQLiteManager()

    def validate(self, menssage: dict) -> bool:
        """Valida un mensaje TLE."""
        if menssage["norad_id"] in self.get_satellites_planificados():
            if self.validate_tle_format(menssage):
                if self.is_latest_tle(menssage):
                    return True
        return False

    def get_satellites_planificados(self):
        """
        Obtiene los satélites planificados desde el archivo PlanningDB
        Consulta al cache por la planificacion y devuelve una lista de norad_id
        """
        return self.sqlite_manager.get_satellites_planificados()

    def validate_tle_checksum(self, tle_line) -> bool:
        """
        Verifica el checksum de una línea TLE (Line 1 o Line 2).
            - Números (0 al 9): se suman directamente.
            - Guiones (-): cuentan como 1.
        Retorna True si el checksum es válido.
        """
        if len(tle_line) < 69:
            return False
        line_data = tle_line[:68]
        expected_checksum = int(tle_line[68])

        total = 0
        for char in line_data:
            if char.isdigit():
                total += int(char)
            elif char == '-':
                total += 1
        return total % 10 == expected_checksum

    def validate_tle_format(self, tle : dict) -> bool:
        """Verifica el formato del TLE y el CRC"""
        #satellite_name = self.satellite_config["satellite_altername"] if self.satellite_config["satellite_altername"] else self.satellite_config["satellite_name"]
        try:
            if len(tle['line1']) == 69 and len(tle['line2']) == 69:
                if self.validate_tle_checksum(tle['line1']) and self.validate_tle_checksum(tle['line2']):
                    return True
        except KeyError as e:
            self.logger.error("Error al validar, el json es incorrecto: %s",e)
        return False

    def tle_epoch_to_datetime(self, epoch_str):
        """Funcion que convierte el epoch del tle a formato datetime"""
        self.logger.debug("epoch: %s",epoch_str)
        pattern = r"^\d{5}\.\d{8}$"
        if re.fullmatch(pattern, epoch_str) is not None:
            year = int(epoch_str[:2])
            year += 2000 if int(epoch_str[:2]) < 57 else 1900  # Según norma NORAD
            day_of_year = float(epoch_str[2:])
            day_int = int(day_of_year)
            day_frac = day_of_year - day_int
            return datetime(year, 1, 1) + timedelta(days=day_int - 1, seconds=day_frac * 86400)

    def is_latest_tle(self, tle : dict) -> bool:
        """Verifica que el TLE sea el ultimo"""
        last_tle_in_db = self.sqlite_manager.get_last_tle(tle['norad_id'])

        if (last_tle_in_db[1].strip() != tle['line1'] or last_tle_in_db[2].strip() != tle['line2']):
            self.logger.debug("El TLE es diferente al anterior. Lineas: %s TLE nuevo: %s", last_tle_in_db, tle)
            old_tle_date = self.tle_epoch_to_datetime(last_tle_in_db[1].strip().split()[3])
            new_tle_date = self.tle_epoch_to_datetime(tle['line1'].split()[3])
            if new_tle_date > old_tle_date:
                self.logger.debug("Comparacion de Epoch Validado = OK")
                self.logger.info("Nuevo TLE - UPSERT en la BD")
                self.sqlite_manager.upsert_tle(tle=tle)
                return True
            self.logger.debug("Comparacion de Epoch Validado = Err -> TLE con epoch menor al anterior")
        self.logger.debug("TLE ya recibido, rechazando....")
        return False

class ValidatePlann():
    """Clase para validar mensajes entrantes de Kafka."""
    #| Validación                                 | ¿Cómo hacerlo?                                                                |
    #| ------------------------------------------ | ----------------------------------------------------------------------------- |
    #|   Que el `TaskID` sea único                | Comparar contra tareas ya enviadas (guardadas localmente o en la BD).         |
    #|   Que el pase aún no haya comenzado        | `start_time > now + margen`                                                   |
    #|   Que el tiempo esté en formato `YYYY DDD` | Usar `strftime("%Y %j %H:%M:%S")`                                             |
    #|   Que el satélite tenga TLE actualizado    | Verificar en tu cache o repositorio de TLE                                    |
    #|   Que la elevación máxima sea > 0°         | Calcular el pase con TLE y posición de la antena                              |
    #|   Que no haya conflicto de recursos        | Consultar tu planificación local / simulador de antena                        |
    #|   Que la antena esté disponible            | Validar que no esté en mantenimiento, reserva o fuera de servicio             |
    #|   Que el XML esté bien formado             | Usar validación contra el esquema `schedule.xsd` (opcional pero útil)         |
    #|   Que el nombre del archivo sea válido     | Validar con regex: `^[a-zA-Z0-9_.]{1,36}$` y no incluya `.done` ni especiales |

    def __init__(self, logger: logging):
        self.logger = logger

    def validar_tle(self, msg: dict):
        """Valida un mensaje TLE."""
        # Implementar la logica de validacion del TLE

    def validate_start_time(self, start_str):
        """Valida que el tiempo de inicio sea al menos 5 minutos en el futuro."""
        start_dt = datetime.strptime(start_str, "%Y %j %H:%M:%S")
        return start_dt > datetime.utcnow() + timedelta(minutes=5)

    def has_conflict(self):
        """Verifica si hay conflictos de actividades en la ventana de tiempo especificada."""
        actividades = self.get_actividades_en_ventana()
        return len(actividades) > 0

    def get_actividades_en_ventana(self):
        """Obtiene las actividades programadas en la ventana de tiempo especificada."""
        # Implementar la logica para obtener las actividades
        # Consulta a la base de datos o cache por las actividades
        return ['plann1', 'plann2']  # Ejemplo de actividades programadas

    def validate_task(self, task: dict):
        """Valida que los campos requeridos estén según la acción"""
        action = task.get("action")
        if action == "ADD":
            required = ["task_id", "satellite", "config_id", "antenna_id", "start", "end"]
        elif action == "CANCEL":
            required = ["task_id"]
        elif action == "PURGE":
            required = []  # solo action
        else:
            raise ValueError(f"Acción no reconocida: {action}")

        for field in required:
            if field not in task:
                raise ValueError(f"Campo requerido '{field}' faltante en tarea con acción {action}")

    def format_vfi_time(dt: datetime) -> str:
        """Validar el formato de fecha"""
        #"""Convierte datetime a formato VFI: YYYY DDD HH:MM:SS"""
        return dt.strftime("%Y %j %H:%M:%S")
