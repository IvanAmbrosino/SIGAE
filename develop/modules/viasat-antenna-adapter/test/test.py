"Tests Unitarios de las funciones"
import sys
import os

from src.connections import Connections
from src.format_tle import FormatTle

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

PASSWD_DIR = "/home/iambrosino/viasat-tle-sender/test/passwd"


class test_format_tle():

    def __init__(self):
        self.format_tle = FormatTle(Logger())

        if self.output_format():    print("output_format: PASS")
        if self.empty_input():      print("empty_input: PASS")
        if self.same_format():      print("same_format: PASS")
        if self.input_types():      print("input_types: PASS")
        if self.keys_names():       print("keys_names: PASS") 

    def output_format(self):
        tle_to_format = {
            "name": "SAOCOM-1A",
            "line1": "1 43641U 18076A   24294.89974537 0.00000111  00000-0 014188-4 0    04",
            "line2": "2 43641  97.8887 109.4672 0001393  83.8212 141.0691 14.82130712    07",
        }
        correct_tle = {
            "name": "SAOCOM-1A",
            "line1": "1 43641U 18076A   24294.89974537  .00000111  00000-0  14188-4 0    04",
            "line2": "2 43641  97.8887 109.4672 0001393  83.8212 141.0691 14.82130712    07",
        }
        tle_formated = self.format_tle.format_tle(json_tle=tle_to_format)
        assert tle_formated == correct_tle, "Error, el tle formateado no corresponde al esperado"

        return True

    def same_format(self):
        tle_to_format = {
            "name": "SAOCOM-1A",
            "line1": "1 43641U 18076A   24294.89974537  .00000111  00000-0  14188-4 0    04",
            "line2": "2 43641  97.8887 109.4672 0001393  83.8212 141.0691 14.82130712    07",
        }
        correct_tle = {
            "name": "SAOCOM-1A",
            "line1": "1 43641U 18076A   24294.89974537  .00000111  00000-0  14188-4 0    04",
            "line2": "2 43641  97.8887 109.4672 0001393  83.8212 141.0691 14.82130712    07",
        }
        tle_formated = self.format_tle.format_tle(json_tle=tle_to_format)
        assert tle_formated == correct_tle, "Error, el tle formateado no corresponde al esperado"

        return True

    def input_types(self):
        tle_to_format = [
            """"name": "SAOCOM-1A",
            "line1": "1 43641U 18076A   24294.89974537  .00000111  00000-0  14188-4 0    04",
            "line2": "2 43641  97.8887 109.4672 0001393  83.8212 141.0691 14.82130712    07","""
        ]
        tle_formated = self.format_tle.format_tle(json_tle=tle_to_format)
        assert not tle_formated, "Error, el resultado debe ser {}"

        tle_to_format = """"name": "SAOCOM-1A",
            "line1": "1 43641U 18076A   24294.89974537  .00000111  00000-0  14188-4 0    04",
            "line2": "2 43641  97.8887 109.4672 0001393  83.8212 141.0691 14.82130712    07","""
        tle_formated = self.format_tle.format_tle(json_tle=tle_to_format)
        assert not tle_formated, "Error, el resultado debe ser {}"

        return True

    def keys_names(self):
        tle_to_format = {
            "names": "SAOCOM-1A",
            "line12": "1 43641U 18076A   24294.89974537  .00000111  00000-0  14188-4 0    04",
            "line23": "2 43641  97.8887 109.4672 0001393  83.8212 141.0691 14.82130712    07",
        }
        tle_formated = self.format_tle.format_tle(json_tle=tle_to_format)
        assert not tle_formated, "Error, el resultado debe ser {}"

        return True

    def empty_input(self):
        tle_formated = self.format_tle.format_tle(json_tle={})
        assert not tle_formated, "Error en la respuesta vacia esperada"

        return True

class Logger():
    def __init__(self):
        self.file = "test.logs"
    def error(self,*args):
        with open(self.file,'a',encoding='utf-8') as f:
            f.write(f'{args[0]}\n')
    def info(self,*args):
        with open(self.file,'a',encoding='utf-8') as f:
            f.write(f'{args[0]}\n')

class test_connections():
    """
    Funciones que validan la conexion y el envio del archivo.
    No valida la aceptacion del TLE por parte de la antena
    """
    def __init__(self):
        logger = Logger()
        self.conn = Connections(logger=logger, base_dir='/home/iambrosino/viasat-tle-sender/src/')
        self.conn.tle_filename = "/test_connection.txt"
        self.conn.await_time = 1
        self.tle = {
            "name": "TEST-TLE",
            "line1": "1 43641U 18076A   24294.89974537  .00000111  00000-0  14188-4 0    04",
            "line2": "2 43641  97.8887 109.4672 0001393  83.8212 141.0691 14.82130712    07",
        }
        with open(file=f'{self.conn.local_tmp}{self.conn.tmp_archive}',mode='w',encoding='utf-8') as f:
            f.write(f"{self.tle['name']}\n{self.tle['line1']}\n{self.tle['line2']}\n")

        if self.direct_conn():          print("direct_conn: PASS")
        if self.tunnel_conn():          print("tunnel_conn: PASS")
        if self.double_tunnel_conn():   print("double_tunnel_conn: PASS")

    def direct_conn(self):
        # --------------- Test Init --------------------- #
        self.conn.config =  {
            "type":"viasat direct",
            "server_config":{
                "server_ip":"10.0.0.253",
                "server_user":"soporte",
                "server_password":f"{PASSWD_DIR}/ssh_password",
                "destination_path":"/home/soporte/remote"
            }
        }
        # --------------- Test Init --------------------- #

        assert not self.conn.post_tle_direct_viasat(), "Error en el evio directo"

        return True

    def tunnel_conn(self):
        # --------------- Test Init --------------------- #
        self.conn.config =  {
            "type":"viasat tunnel",
            "server_config":{
                "server_ip":"172.26.78.203",
                "server_user":"scc",
                "server_password":f"{PASSWD_DIR}/scc_password",
                "destination_path":"etc/remote"
            },
            "server_tunnel":{
                "server_ip":"10.0.0.184",
                "server_user":"admin",
                "server_password":f"{PASSWD_DIR}/tounel_password"
            }
        }
        # --------------- Test Init --------------------- #

        assert not self.conn.post_tle_tunnel_viasat(), "Error en el envio por tunnel"
        return True

    def double_tunnel_conn(self):
        # --------------- Test Init --------------------- #
        self.conn.config =  {
            "type":"viasat duble tunnel",
            "server_config":{
                "server_ip":"172.26.79.46",
                "server_user":"scc",
                "server_password":f"{PASSWD_DIR}/scc_password",
                "destination_path":"etc/remote"
            },
            "server_tunnel":{
                "server_ip":"10.0.5.123",
                "server_user":"scc",
                "server_password":f"{PASSWD_DIR}/scc_password"
            },
            "second_server_tunnel":{
                "server_ip":"172.26.79.83",
                "server_user":"admin",
                "server_password":f"{PASSWD_DIR}/tounel_password"
            }
        }
        # --------------- Test Init --------------------- #

        assert not self.conn.post_tle_double_tunnel_viasat(), "Error por el envio doble tunnel"

        return True


test_format_tle()
test_connections()
