"""Modulo adaptador que contiene la logica de donde se saca el listado de satelites"""
from datetime import datetime, timedelta
import pymssql
from config_manager import ConfigManager

class GetSatellitesCsv:
    """Clase que obtiene el listado de satelites de un archivo .csv"""
    def __init__(self, list_satellites_file):
        self.list_satellites_file = list_satellites_file
        self.list_satellites = self.load_satellites()

    def load_satellites(self):
        """Carga la lista de satelites desde el archivo de configuracion"""
        try:
            with open(self.list_satellites_file,'r',encoding='utf-8') as file:
                list_satellites = file.readlines()
            return list_satellites
        except (IOError,OSError) as err:
            print('Error reading configuration file -> %s. Error -> %s',self.list_satellites, err)
        return []

class GetSatellitesXPlann():
    """
    Clase que obtiene el listado de satelites asignado a la antena
    """
    def __init__(self):
        """Initialize the class with the database connection details."""
        self.configs     = ConfigManager().config["database"]
        self.host        = self.configs["host"]
        self.user        = self.configs["user"]
        self.passwd      = self.configs["password"]
        self.db          = self.configs["bbdd"]
        self.conn = None
        self.cur = None
        try:
            self.con_database(dict = True)
            satellites = self.get_satellites()
            planificacion = self.get_planificacion()
            antenas = self.consulta_antenas()
            macros = self.consulta_macros()

            self.filtrar_pasadas(configuraciones = macros,resultado = planificacion,antenas = antenas)
        except Exception as e:
            print(e)


    def con_database(self, dict = False):
        """Funcion que crea la conexion a la base de datos"""
        self.conn = pymssql.connect(self.host,
                               self.user,
                               self.passwd,
                               self.db['bbdd'],
                               tds_version="7.0",
                               charset="UTF-8"
                               )
        self.cur = self.conn.cursor(as_dict=dict)
    
    def con_close(self):
        """Funcion que cierra la conexion a la base de datos"""
        if self.conn:
            self.conn.close()
            self.cur = None
            self.conn = None

    def get_satellites(self,):
        """
        Make the connection to the MSSQL DB and set satellites.
        """
        self.cur.execute(f"SELECT * FROM [{self.db['bbdd']}].dbo.[{self.db['table']}] where [eliminado] = 'N'")
        satellites = self.cur.fetchall()
        return satellites

    def get_planificacion(self):
        """
        Realiza la consulta a la bbdd para obtener las actividades planificadas.
        """
        hora_actual = (datetime.utcnow() - timedelta(hours = 6)).strftime('%Y-%m-%dT%H:%M:%S')
        hora_limite = (datetime.utcnow() + timedelta(hours = 24)).strftime('%Y-%m-%dT%H:%M:%S')
        query = "SELECT [Satelite], [Orbita], [FechaHoraInicial], [FechaHoraFinal], [idMacro], [configuracion],[Estado] FROM [%s].[dbo].[%s] WHERE [FechaHoraInicialProgramada] >= '%s' AND [FechaHoraFinalProgramada] <= '%s' AND [Estado] = 'A' ORDER BY FechaHoraInicialProgramada ASC", \
            self.configs['planificacion']['bbdd'],self.configs['planificacion']['tabla plan'],hora_actual,hora_limite

        self.cur.execute(query)  #Ejecuta la consulta
        pasadas = self.cur.fetchall()
        return pasadas

    def consulta_antenas(self):
        """
        Obtiene el identificador y nombre de la antena.
        """
        self.cur.execute("SELECT * FROM [%s].[dbo].[%s] where [eliminado] <> 'S'",self.configs['planificacion']['bbdd'],self.configs['planificacion']['tabla ant'])
        lista_antenas = []
        for antena in self.cur:
            lista_antenas.append([antena[0],antena[1]])
        return lista_antenas

    def consulta_macros(self):
        """
        Consulta la antena con las diferentes macros.
        """
        self.cur.execute("SELECT * FROM [%s].[dbo].[%s]",self.configs['planificacion']['bbdd'],self.configs['planificacion']['tabla conf'])
        lista_configuraciones = []
        for configuracion in self.cur:
            lista_configuraciones.append(configuracion)
        return lista_configuraciones

    def filtrar_pasadas(self, configuraciones,resultado,antenas):
        """ Obtiene las pasadas que se ejecutaran por antena definida en conf.get('planificacion','unidad') """
        #~ Lista donde guardo las pasadas
        pasadas = []
        tles = []
        #~ Itero todas las pasadas planificadas en el rango de tiempo de la consulta SQL.
        for pasada in enumerate(resultado):
            #~ Itero el total de configuraciones.
            print("resultado[pasada]: ",resultado[pasada])
            for configuracion in configuraciones:
                #~ Analizo si coincide con la configuracion de la pasada
                if configuracion[0] == resultado[pasada][5]: # Si son la misma configuracion
                    print("resultado[pasada][5]: ",resultado[pasada][5])
                    print("configuracion[0]: ",configuracion[0])
                    #~ Sobre el conjunto de antenas.
                    for antena in antenas:
                        if int(configuracion[2]) == int(antena[0]):
                            print(("configuracion[2): ",configuracion[2]))      # Configuracion de la antena
                            print(("int(antena[0]): ",int(antena[0])))          # Identificador de la antena
                            print((self.configs['planificacion']['unidad']))    # Unidad de antena configurada
                            print((antena[1].split()))
                        # Aca tendria que buscar el satelite que va a ser trakeado por la antena.

                        
                        if int(configuracion[2]) == int(antena[0]) and (self.configs['planificacion']['unidad'] in antena[1].split()):
                            print(("Coincidencia de antena: ",antena[1]))
                            if (resultado[pasada][4] == configuracion[8] or resultado[pasada][4] == configuracion[9] or
                            resultado[pasada][4] == configuracion[10] or resultado[pasada][4] == configuracion[11]): #Si corresponde a la antena
                                print(("resultado[pasada]: ",resultado[pasada]))
                                try:
                                    pasadas.index(resultado[pasada])
                                    break
                                except ValueError as e:
                                    resultado[pasada].insert(len(resultado[pasada]),'relax')
                                    pasadas.append(resultado[pasada])   #La guardo en la lista para pasarla a la siguiente funcion
                                    print("Guarda para enviar a la antena la pasada %s. %s" ,resultado[pasada],e)
                                    #try:
                                    #    tles.index(self.consulta_tle(resultado[pasada][0]))
                                    #    break
                                    #except ValueError as ex:
                                    #    tle = self.consulta_tle(resultado[pasada][0])
                                    #    tles.append(tle)
                                    #    print("Guarda para enviar a la antena el tle %s. %s",tle,ex)
                                    #break
                            elif resultado[pasada][4] == configuracion[1]:
                                try:
                                    pasadas.index(resultado[pasada])
                                    break
                                except ValueError as e:
                                    resultado[pasada].insert(len(resultado[pasada]),'extreme')
                                    pasadas.append(resultado[pasada])   #La guardo en la lista para pasarla a la siguiente funcion
                                    print("Guarda para enviar a la antena la pasada %s.%s",(resultado[pasada]),e)
                                    #try:
                                    #    tles.index(self.consulta_tle(resultado[pasada][0]))
                                    #    break
                                    #except ValueError as ex:
                                    #    tle = self.consulta_tle(resultado[pasada][0])
                                    #    tles.append(tle)
                                    #    print("Guarda para enviar a la antena el tle %s." ,tle,ex)
                                    #break
        return pasadas,tles  #retorna la lista con las pasadas filtradas
