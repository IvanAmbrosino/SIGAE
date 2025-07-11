"""Modulo que procesa mensajes entrantes de Kafka."""
import logging
from datetime import datetime, timedelta


class ProcessMessage:
    """Clase para procesar mensajes entrantes de Kafka."""
    def __init__(self,logger: logging):
        self.logger = logger

    def process_message(self, msg: dict, ):
        """Procesa los mensajes recibidos de Kafka y determina su tipo para poder ser procesado."""
        if msg["type"] == "tle":
            #validar_tle(msg)
            #make_tle_file(msg)
            #send_tle_file(msg)
            pass
        elif msg["type"] == "plan":
            #validar_plan(msg)
            #make_plann_file(msg)
            #send_plann_file(msg)
            pass
        elif msg["type"] == "plan+tles":
            #validar_plan_con_tle(msg)
            #make_tle_file(msg)
            #send_tle_file(msg) # primero debe enviar el TLE
            #make_plann_file(msg)
            #send_plann_file(msg)
            pass

class ValidarTLE():
    """Clase para validar mensajes TLE entrantes de Kafka."""
    def __init__(self, logger: logging):
        self.logger = logger

    def validate_tle(self, msg: dict):
        """Valida un mensaje TLE."""
        get_satellites_planificados = self.get_satellites_planificados()
        if msg["norad_id"] in get_satellites_planificados:
            return True
        else:
            return False

    def get_satellites_planificados(self):
        """Obtiene los satélites planificados desde el archivo PlanningDB."""
        # Implementar la lógica para obtener los satélites planificados
        # Consulta al cache por la planificacion
        return ["25544", "46265"]






class ValidarPlann():
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

    def has_conflict(self, start, end, antenna_id):
        """Verifica si hay conflictos de actividades en la ventana de tiempo especificada."""
        actividades = self.get_actividades_en_ventana()
        return len(actividades) > 0

    def get_actividades_en_ventana(self):
        """Obtiene las actividades programadas en la ventana de tiempo especificada."""
        # Implementar la logica para obtener las actividades
        # Consulta a la base de datos o cache por las actividades
        return ['plann1', 'plann2']  # Ejemplo de actividades programadas
