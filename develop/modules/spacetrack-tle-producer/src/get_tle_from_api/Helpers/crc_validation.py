def validate_tle_checksum(tle_line) -> bool:
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