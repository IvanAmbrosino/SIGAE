"""Modulo que contiene las validaciones de un TLE"""
import logging

class CheckTle:
    """Clase que valida un TLE"""
    def __init__(self, logger : logging.Logger):
        self.logger = logger

    def validate_tle_length(self, tle : dict) -> bool:
        """Verifica la cantidad de caracteres del TLE"""
        try:
            if len(tle['line1']) == 69 and len(tle['line2']) == 69:
                return True
        except KeyError as e:
            self.logger.error(f"Error: Missing key in TLE dictionary - {e}")
            return False

    def validate_tle_checksum(self, tle_line) -> bool:
        """
        Verifica el checksum de una línea TLE (Line 1 o Line 2).
            - Números (0 al 9): se suman directamente.
            - Guiones (-): cuentan como 1.
        Retorna True si el checksum es válido.
        """
        try:
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
        except (ValueError, IndexError) as e:
            self.logger.error(f"Error validating checksum: {e}")
            return False

    def is_valid(self, tle: dict) -> bool:
        """Comprueba si el TLE es válido."""
        if not self.validate_tle_length(tle):
            self.logger.error("TLE length is invalid.")
            return False
        if not self.validate_tle_checksum(tle['line1']):
            self.logger.error("TLE Line 1 checksum is invalid.")
            return False
        return True
