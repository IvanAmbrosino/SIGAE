#!/usr/bin/python3
from redis import Redis, RedisError
import logging
import logging.handlers as handlers

logger = logging.getLogger('schedule-client')


def set_cache_activities(task, data, r, conf):
    """Almaceno en el cache las actividades"""
    logger.info("Almacenando actividad en la cache")
    try:
        r.hset(task, mapping=data)
        r.expire(name=task, time=conf["ttl_hours"]*3600)
        logger.info("Almacena %s: %s",task, data)
    except RedisError as error:
        print(error)
        exit()
    return


def get_cache_activities(r, task_id):
    """Recupero datos de la cache de actividades"""
    # print("task id: ", task_id)
    return r.hgetall(task_id)


def set_cache_index(r,task, data):
    """Setea el index"""


def connect(conf):
    """Conecta a la cache"""
    try:
        r = Redis(host=conf['host'], port=conf['port'])
        print(r)
        return r
    except RedisError as err:
        print(err)
        exit()
