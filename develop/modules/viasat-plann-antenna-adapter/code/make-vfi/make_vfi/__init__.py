#!/usr/bin/python3
from datetime import datetime, timezone
from json import load
from requests import get
from make_vfi.xml_ops import OpsOverXML as XML


def make_vfi_sched(activities, unit, action, filename, path):
    """Programa que ejecuta la planificacion usando el VFI para Viasat"""
    root = XML().create_root()
    XML().add_task(root, activities, unit, action)
    XML().write_file(root, filename, path)
