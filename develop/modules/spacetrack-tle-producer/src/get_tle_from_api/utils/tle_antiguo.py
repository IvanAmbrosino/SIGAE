from datetime import datetime, timezone, timedelta


def tle_antiguo(timestamp: int, xxxx) -> bool:
    """Valida si el TLE es más antiguo que uno guardado"""
    tle_date = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
    return (datetime.now(timezone.utc) - tle_date) > xxxx