"""Module that validates the different types of messages"""
import re
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone

from infraestructure.sqlite_manager import SQLiteManager # pylint: disable=import-error
from infraestructure.config_manager import ConfigManager # pylint: disable=import-error

class Validator(ABC):
    """Abstract class to define the validation strategy"""

    @abstractmethod
    def validate(self, message: dict, chequeo: bool = True) -> bool:
        """Obtiene un archivo al servidor SFTP"""

class ValidateTLE(Validator):
    """Class to validate TLE messages"""
    def __init__(self, logger: logging):
        self.logger = logger
        self.sqlite_manager = SQLiteManager()

    def validate(self, message: dict, chequeo: bool = True) -> bool:
        """
        Valida un mensaje TLE.
            - Si el chequeo esta activo, solamente acepta TLEs de satelites que tiene planificados
            - En caso de estar desactivado se aceptan todos los TLE entrantes
        Validaciones:
            - Validacion del formato del TLE, con sus campos y CRC
            - Compara con los guardados para saber si es el ultimo o mas nuevo.
        """
        if chequeo:
            list_sat_planificados = self.get_satellites_planificados()
            if message["norad_id"] in list_sat_planificados:
                self.logger.debug("Se verifica que el satelite se encuentra planificado para el TLE %s",message['satellite_name'])
                if self.validate_tle_format(message):
                    if self.is_latest_tle(message):
                        self.logger.debug("Mensaje correctemente validado")
                        return True
                    self.logger.debug("No hay cambios en el TLE.")
                self.logger.error("TLE con formato incorrecto.")
            self.logger.info("No hay planificacion presente para ese TLE, rechazando.")
            self.logger.debug("Lista de satelites planificados en esta unidad: %s",list_sat_planificados)
            return False
        else:
            if self.validate_tle_format(message):
                if self.is_latest_tle(message):
                    return True
                self.logger.debug("No hay cambios en el TLE.")
            self.logger.error("TLE con formato incorrecto.")
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
        try:
            if len(tle['line1']) == 69 and len(tle['line2']) == 69:
                if self.validate_tle_checksum(tle['line1']) and self.validate_tle_checksum(tle['line2']):
                    self.logger.debug("Se valida correctemente el formato del TLE y el CRC")
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
        self.logger.error("Error al convertir el epoch a datetime")
        return None

    def is_latest_tle(self, tle : dict) -> bool:
        """Verifica que el TLE sea el ultimo comparando el contenido y las fechas de epoch"""
        last_tle_in_db = self.sqlite_manager.get_last_tle(tle['norad_id'])
        if not last_tle_in_db:
            self.logger.debug("Es el primer TLE que llega, aceptando y guardando en la BD")
            return True
        if (last_tle_in_db[0].strip() != tle['line1'] or last_tle_in_db[1].strip() != tle['line2']):
            old_tle_date = self.tle_epoch_to_datetime(last_tle_in_db[0].strip().split()[3])
            new_tle_date = self.tle_epoch_to_datetime(tle['line1'].split()[3])
            if new_tle_date > old_tle_date:
                self.logger.debug("Se valida que es un nuevo TLE")
                self.logger.debug("[OLD TLE]: %s\n%s \n%s ", tle['satellite_name'], last_tle_in_db[0], last_tle_in_db[1])
                self.logger.debug("[NEW TLE]: %s\n%s \n%s ", tle['satellite_name'], tle['line1'], tle['line2'])
                self.sqlite_manager.upsert_tle(tle=tle)
                return True
            self.logger.debug("TLE con epoch menor al anterior %s > %s",old_tle_date,new_tle_date)
        self.logger.debug("El TLE ya fue recibido, rechazando.")
        return False

class ValidatePlann(Validator):
    """Clase para validar mensajes entrantes de Kafka."""
    #| Validación                                 | ¿Cómo hacerlo?                                                                |
    #| ------------------------------------------ | ----------------------------------------------------------------------------- |
    #|   Que el msg este destinado a la antena    | Comparar el destination unit del mensaje con el configurado.                  | x
    #|   Que el `TaskID` sea único                | Comparar contra tareas ya enviadas (guardadas localmente o en la BD).         | x
    #|   Que el pase aún no haya comenzado        | `start_time > now + margen`                                                   | x
    #|   Que el tiempo esté en formato `YYYY DDD` | Usar `strftime("%Y %j %H:%M:%S")`                                             | x
    #|   Que el satélite tenga TLE actualizado    | Verificar en tu cache o repositorio de TLE                                    | x
    #|   Que no haya conflicto de recursos        | Consultar tu planificación local / simulador de antena                        | x
    #|   Que el nombre del archivo sea válido     | Validar con regex: `^[a-zA-Z0-9_.]{1,36}$` y no incluya `.done` ni especiales | x

    def __init__(self, logger: logging):
        self.logger = logger
        self.sqlite_manager = SQLiteManager()
        self.configs = ConfigManager().load_config()

    def validate(self, message: dict, chequeo: bool = True) -> bool:
        """
        Valida un mensaje Planificacion
            - Valida que el mensaje este dirigido a la antena
            - Si chequeo esta activo, valida que haya TLE actualizado
        Rechaza toda tarea que:
            - Tenga un mismo ID que una tarea ya cargada
            - Que tenga pasadas que estan sucediento o ya pasaron
            - Que no contenga los campos necesarios para ejecutar el tipo de tarea
            - Que no tenga las fechas en el formato requerido
            - Que no posea un TLE actualizado
        """
        antenna_id = self.configs['app']['antenna_id']
        if message.get('antenna_id') != antenna_id:
            self.logger.debug("Mensaje rechazado para antena distinta: %s", message.get('antenna_id'))
            return False

        self.logger.info("Mensaje entrante para la antena: %s", message['antenna_id'])
        for task in message.get('plan', []):

            if not self.validate_task(task):
                self.logger.warning("Tarea inválida: el mensaje no contiene los campos requeridos por la accion -> %s", task)
                return False

            if self.unique_task_id(task['task_id']):
                self.logger.warning("ID de tarea no única: %s", task['task_id'])
                return False

            try:
                task['start'] = self.validate_isoformat(task['start'])
                task['end'] = self.validate_isoformat(task['end'])
            except ValueError as e:
                self.logger.error("Error formateanfo fecha: %s",e)
                return False

            if not self.validate_start_time(task['start']):
                self.logger.warning("Hora de inicio inválida: %s", task['start'])
                return False

            if self.has_conflict(task):
                self.logger.warning("Conflicto detectado con tarea: %s. Existen actividades planificadas en esa ventana", task['task_id'])
                return False

            if chequeo and not self.validate_freshness_tle(task['norad_id']):
                self.logger.warning("TLE desactualizado para NORAD ID: %s", task['norad_id'])
                return False

        return True


    def unique_task_id(self, task_id: str) -> bool:
        """
        Consulta en la BD si existe alguna plann con ese id
            - devuelve True si existe una con ese ID
            - devuelve False si no existe una task con ese ID
        """
        exists = self.sqlite_manager.pase_ya_programado(task_id)
        self.logger.debug("Existe la tarea en la bd? -> %s",exists)
        return exists

    def validate_freshness_tle(self, norad_id):
        """Consulta en la bd si existe un TLE para la pasada"""
        tles = self.sqlite_manager.get_freshness_tle(norad_id, freshness_hours=self.configs['app']['freshness_hours_tle'])
        if tles:
            return True
        self.logger.error("No se encuentran TLEs Frescos: %s",tles)
        return False


    def validate_start_time(self, start_dt: datetime) -> bool:
        """Valida que el tiempo de inicio sea al menos 5 minutos en el futuro."""
        self.logger.debug("Comparacion de fechas: start_dt_task: %s > now: %s",
                          start_dt ,datetime.now(timezone.utc) + timedelta(minutes=self.configs['app']['minutes_min_to_load']))
        return start_dt > datetime.now(timezone.utc) + timedelta(minutes=self.configs['app']['minutes_min_to_load'])

    def has_conflict(self,task: dict) -> bool:
        """Verifica si hay conflictos de actividades en la ventana de tiempo especificada."""
        return self.sqlite_manager.exist_passes_in_window(task['start'],task['end'])

    def validate_isoformat(self, date_str: str) -> datetime:
        """Traduce los horarios al isoformat"""
        try:
            dt = datetime.fromisoformat(date_str)
            return dt
        except ValueError as e:
            raise ValueError(f"La fecha '{date_str}' no está en formato ISO 8601 válido.") from e

    def validate_task(self, task: dict):
        """Valida que los campos requeridos estén según la acción"""
        action = task['action']
        if action == "ADD":
            required = ["task_id", "satellite", "antenna_id", "config_id", "norad_id", "start", "end", "prepass_seconds", "postpass_seconds"]
        elif action == "CANCEL":
            required = ["task_id"]
        elif action == "PURGE":
            required = []  # solo action
        else:
            raise ValueError(f"Acción no reconocida: {action}")

        for field in required:
            if field not in task:
                self.logger.warning("Campo requerido '%s' faltante en tarea con acción %s",field,action)
                return False
        self.logger.debug("Contiene todos los campos necesarios")
        return True

    def format_vfi_time(self, dt: datetime) -> str:
        """Validar el formato de fecha"""
        #"""Convierte datetime a formato VFI: YYYY DDD HH:MM:SS"""
        return dt.strftime("%Y %j %H:%M:%S")
