#!/usr/bin/python3
from json import load
from datetime import datetime, timezone
from requests import get
import requests
import  make_vfi
import cache_ops
from manage_files import ManageFile as MF
from xml.dom.minidom import parse
import logging
import logging.handlers as handlers

logger = logging.getLogger('schedule-client')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logHandler = handlers.TimedRotatingFileHandler('logs/schedule_client.log', 
                                               when='D', interval=1, 
                                               backupCount=2)
logHandler.setLevel(logging.INFO)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)


def load_config(config_file):
    """Carga el archivo de configuracion"""
    with open(config_file, 'r', encoding='utf-8') as fp:
        data = load(fp)
        return data["VFI"]


def make_url(config_data) -> str:
    """Devuelve la URL para consultar actividades.
    Deberia del otro lado poder diferenciar por antena usando
    este parametro {"unit": config_data["unit"]}"""
    return f"{config_data['api']['url']}{config_data['api']['unit']}"


def make_file(passes, cfg):
    """Construye el archivo llamando a la libreria.

    Args:
        passes (dict): json dict en el formato que lo devuevle la API Antenna 
        Scehdule cfg (_type_): Puntero del archivo de configuracion

    Returns:
        _type_: True si termina de construir el archivo.
    """
    print(passes)
    exit()
    utc = datetime.now(timezone.utc)
    fn = f"rciSched_{utc.strftime('%Y-%j_%H%M')}.xml"
    make_vfi.make_vfi_sched(activities=passes, unit=cfg["api"]["unit"],
                            filename=fn, path=cfg["local"]["workdir"])
    # MF().put_rciSched(cfg["destination"]["host"], cfg["destination"]["user"],
    #                   cfg["destination"]["pswd"],
    #                   cfg["destination"]["path"],
    #                   f'{cfg["local"]["workdir"]}/{fn}')
    return True


def check_new_vs_old_activities(cfg, activities, r):
    """Traigo las  actividades ua cargadas en el importSched para el dia de
    hoy.
    Si no existe creo uno nuevo. Si existe comparo las viejas con las nuevas,
    borro o hago update."""
    # Recupero el archivo
    file_list = MF().get_sched(host=cfg["destination"]["host"],
                               user=cfg["destination"]["user"],
                               passwd=cfg["destination"]["pswd"],
                               path=cfg["destination"]["path"],
                               outpath=cfg["local"]["workdir"],
                               mask=datetime.now(
                                   timezone.utc).strftime("importSched_%Y-%j")
                               )
    logger.info("Recupera archivo de la SCC: {%s}", file_list)
    cache_data = {}
    for activity in activities:
        task_id = format_cache_key(activities[activity])
        cache_data[task_id] = activities[activity]
        # print("Get cache activities: ", 
        #       cache_ops.get_cache_activities(r, task_id))
        if not cache_ops.get_cache_activities(r, task_id):
            logger.info("Cargando en cache %s.", task_id)
            cache_ops.set_cache_activities(task_id, cache_data[task_id], r,
                                           cfg["cache"])
    # Lista de actividades ya cargadas en la antena
    # activities_in_antena = []
    # Recupero satelite, orbita, aos y los
    # for rci in file_list:
    #     parser_xml(cfg, rci)
    #     exit()


def format_cache_key(activity):
    """Formatea cada JSON para almacenar los datos"""
    return f'{activity["Satelite"]}:{activity["Orbita"]}'


def parser_xml(cfg, rci):
    """Parseo el archivo de schedule XML"""
    dom = parse(f'{cfg["local"]["workdir"]}/{rci}')  # parse an XML file by name
    logger.info("Parsea el importSched")
    print(dom)
    print(dom.nodeName)
    for node in dom.getElementsByTagName('TaskID'):
        print(node.firstChild.nodeValue)



def get_api_data(cfg):
    """Make query to API Antenna"""
    return get(f'{cfg["api"]["url"]}{cfg["api"]["unit"]}', timeout=2).json()


def __init__():
    """Inicia la consulta y envio de schedule para la unidad configurada"""
    logger.info('Schedule Client Started')
    headers = {"Content-Type":"application/json"}
    config_data = load_config("configuration.json")
    response = requests.get(make_url(config_data), headers=headers,
                            timeout=5)
    # print(response.json())
    r = cache_ops.connect(config_data["cache"])
    check_new_vs_old_activities(config_data, response.json(), r)
    exit()
    make_file(response.json(), config_data)


if __name__ == "__main__":
    __init__()
