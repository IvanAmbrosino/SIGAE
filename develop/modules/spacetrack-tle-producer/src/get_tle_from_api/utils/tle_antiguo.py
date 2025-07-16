from datetime import datetime, timezone, timedelta


def tle_antiguo(timestamp: int, ultimo: int) -> bool:
    """Valida si el TLE es más antiguo que uno guardado"""

    if timestamp < ultimo:
        return True

    return False