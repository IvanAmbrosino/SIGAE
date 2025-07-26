"""Modulo encargado de obtener el listado de planificacion para enviar"""
import logging
from pprint import pprint
from infraestructure.config_manager import ConfigManager # pylint: disable=import-error
from infraestructure.database_manager import DatabaseManager # pylint: disable=import-error
from application.make_message import MakeMessage # pylint: disable=import-error
from domain.class_domain import Activities # pylint: disable=import-error

class PlanningManager():
    """Clase principal para la obtencion de la planificacion y validacion de la misma"""
    def __init__(self, logger: logging):
        self.config_manager = ConfigManager()
        self.configs = self.config_manager.load_config()
        self.logger = logger
        self.db_configs = self.configs['database']
        self.make_message = MakeMessage(logger= logger)
        self.database_manager = DatabaseManager(
            dbname=     self.db_configs["dbname"],
            user=       self.db_configs["user"],
            password=   self.config_manager.read_secret(self.db_configs["password"]),
            host=       self.db_configs["host"]
        )
        self.activities = {}
        self.activities_by_antenna = {}

    def send_planning(self):
        """Funcion que obtiene la planificacion, clasifica las actividades y las envia a las diferentes antenas"""
        self.logger.info("Iniciando proceso de envio de planificacion")
        activities = self.get_planning()
        if not activities:
            self.logger.info("No hay actividades para enviar")
            return

        self.logger.info("Armando listado de actividades estructurado")
        self.activities = Activities(activities).to_dict()

        # Clasificamos las actividades por antena
        self.clasificar_actividades()
        if not self.activities_by_antenna:
            self.logger.info("No hay actividades clasificadas para enviar")
            return

        # Enviamos los mensajes a las antenas
        #for antenna, messages in self.activities_by_antenna.items():
        #    for message in messages:
        #        self.make_message.send_message(antenna, message)

    def get_planning(self):
        """Obtiene la planificacion de actividades a enviar"""
        self.logger.info("Obteniendo actividades para enviar")
        self.database_manager.connect()
        activities = self.database_manager.get_activity_to_send(
            min_hours_required=self.configs['app']['min_hours_required'],
            max_hours_required=self.configs['app']['max_hours_required']
            )
        if not activities:
            self.logger.info("No hay actividades pendientes para enviar")
            return None
        self.database_manager.disconnect()
        return activities

    def clasificar_actividades(self):
        """
        Clasifica actividades según su estado y asignaciones
        
        Returns
        
            - **dict**: Un diccionario con las actividades clasificadas por antena.
        ```
            { "antenna_id": [
                    { 'activity': activity_data, 'assignment': assignment_data o task_data },
                ]
            }
        ```
        """
        clasificacion = {
            'ADD': [],
            'UPDATE': [],
            'DELETE': [],
            'REASSIGN': []
        }

        for actividad_id, data in self.activities.items():
            asignaciones = data['asignaciones'] # TASK
            datos_actividad = data['datos']     # ACTIVITY

            if len(asignaciones) == 1:
                ultima_asignacion = asignaciones[0]
                if ultima_asignacion["antenna_code"] not in self.activities_by_antenna:
                    self.activities_by_antenna[ultima_asignacion["antenna_code"]] = []
                # ---------- Actividades nuevas son ADD ------------- #
                if datos_actividad['status'] == 'authorized':
                    if ultima_asignacion['send_status'] == 'pending' and ultima_asignacion["is_confirmed"] and ultima_asignacion["is_active"]:
                        message_add = self.make_message.make_message_add(datos_actividad, ultima_asignacion) # Creamos el mensaje a enviar
                        self.activities_by_antenna[ultima_asignacion["antenna_code"]].append(message_add) # Agregamos a la lista de mensajes para las diferentes antenas
                        clasificacion['ADD'].append(message_add)
                        continue

            elif len(asignaciones) > 1:

                asignaciones_ordenadas = sorted(asignaciones, key=lambda x: x['assigned_at'], reverse=True) # Ordenar por 'assigned_at' de forma descendente
                ultima_asignacion = asignaciones_ordenadas[0] if len(asignaciones_ordenadas) >= 1 else None
                penultima_asignacion = asignaciones_ordenadas[1] if len(asignaciones_ordenadas) >= 2 else None
                if ultima_asignacion["antenna_code"] not in self.activities_by_antenna:
                    self.activities_by_antenna[ultima_asignacion["antenna_code"]] = []

                # ---------- Actividades canceladas son DELETE ------------- #
                if datos_actividad['status'] == 'canceled':
                    if (
                    ultima_asignacion['send_status'] == 'pending'
                    and ultima_asignacion["is_confirmed"]
                    and ultima_asignacion["is_active"]
                    and penultima_asignacion
                    and penultima_asignacion['send_status'] == 'confirmed'
                    and not penultima_asignacion["is_active"]):
                        message_delete = self.make_message.make_message_delete(datos_actividad, ultima_asignacion) # Creamos el mensaje a enviar
                        self.activities_by_antenna[ultima_asignacion["antenna_code"]].append(message_delete) # Agregamos a la lista de mensajes para las diferentes antenas
                        clasificacion['DELETE'].append(message_delete)
                        continue

                if datos_actividad['status'] == 'authorized':
                    if (
                    ultima_asignacion['send_status'] == 'pending'
                    and ultima_asignacion["is_confirmed"]
                    and ultima_asignacion["is_active"]
                    and penultima_asignacion
                    and penultima_asignacion['send_status'] == 'confirmed'
                    and not penultima_asignacion["is_active"]):
                        # ---------- Actividades REASIGNADAS o MODIFICADAS ------------- #
                        #if ultima_asignacion.antenna != penultima_asignacion["antenna"] or ultima_asignacion.antenna == penultima_asignacion["antenna"]: # REASIGNACION en diferente antena
                        message_reassign = self.make_message.make_message_add(datos_actividad, ultima_asignacion) # Creamos el mensaje a enviar
                        message_delete = self.make_message.make_message_delete(datos_actividad, penultima_asignacion) # Creamos el mensaje a enviar
                        if penultima_asignacion["antenna_code"] not in self.activities_by_antenna:
                            self.activities_by_antenna[penultima_asignacion["antenna_code"]] = []
                        self.activities_by_antenna[ultima_asignacion["antenna_code"]].append(message_delete) # Agregamos a la lista de mensajes para las diferentes antenas
                        if ultima_asignacion["antenna_code"] != penultima_asignacion["antenna_code"]:
                            clasificacion['REASSIGN'].append(message_reassign)
                        else:
                            clasificacion['UPDATE'].append(message_reassign)
                        clasificacion['DELETE'].append(message_delete)

            else:
                self.logger.warning(f"La actividad {actividad_id} no tiene asignaciones")
                continue

        # Test de salida
        print(" --------------------- Envio de actividades --------------------- ")
        for antenna, messages in self.activities_by_antenna.items():
            print(f"Antenna: {antenna}")
            pprint(messages)
        print(" --------------------- Actividades por antena --------------------- ")
        pprint(self.activities_by_antenna)
        print(" --------------------- Clasificacion de actividades --------------------- ")
        pprint(clasificacion)
