"""Modulo que transforma los datos segun el formato requerido por la antena"""
import re

class TransformTle():
    """Clase que tiene las funcionalidades para el formateo de los TLE de saocom"""
    def __init__(self,logger):
        self.logger = logger

    def transform(self, mensaje: dict) -> dict:
        """Funcion que llama a todas las transformaciones del mensaje"""
        return self.format_tle(mensaje)

    def format_tle(self,json_tle) -> dict:
        """
        Funcion que formatea un tle ppm de SAOCOM para que pueda ser cargado en las antenas de Viasat
        Usando el standart para realizar los TLE, reemplazamos los 0 por " " justo donde estan los valores
        """
        if json_tle:
            try:
                # Modificar la Primera derivada de n: el número en la posición 34-43
                json_tle["line1"] = json_tle["line1"][0:32] + re.sub(r'\s0\.(\d+)', r'  .\1', json_tle["line1"][32:43], count=1) + json_tle["line1"][43:69]  # Reemplaza "0." por " ."
                # Modificar el Coeficiente de arrastre: el número en la posición 54-61
                json_tle["line1"] = json_tle["line1"][0:52] + re.sub(r'\s0(\d+[-+]\d+)', r'  \1', json_tle["line1"][52:61], count=1) + json_tle["line1"][61:69]  # Reemplaza "0" por un espacio

                # Verificar la longitud de la línea (debe ser 69 caracteres)
                assert len(json_tle["line1"]) == 69, f"Error: la longitud de la línea 1 es {len(json_tle['line1'])} en lugar de 69."
                return json_tle
            except IndexError as e:
                self.logger.error("Error en el indice del TLE: %s",e)
            except TypeError as e:
                self.logger.error("Error en el Type: %s",e)
            except KeyError as e:
                self.logger.error("Error en la key: %s",e)
            except AssertionError as e:
                self.logger.error(e)
        return {}
