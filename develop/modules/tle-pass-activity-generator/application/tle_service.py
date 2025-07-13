import uuid
from domain.tle_pass import TleData
from infrastructure.db import save_tle_data
import re
from datetime import datetime, timedelta


def get_norad_id(line1: str) -> str:
    match = re.match(r"1\s+(\d{5})U", line1)
    if match:
        return match.group(1)
    raise ValueError("Formato de TLE inválido")



def process_and_save_tle(conn, tle_message: dict):
    line1 = tle_message.get('line1')
    line2 = tle_message.get('line2')
    satellite_id = get_norad_id(line1)  
    epoch = parse_epoch_from_line1(line1)
    
    tle_data = TleData(
        id=str(uuid.uuid4()),
        satellite_id=satellite_id,
        line1=line1,
        line2=line2,
        epoch=epoch,
        source='spacetrack',
        is_valid=True,
    )
    save_tle_data(conn, tle_data)


def parse_epoch_from_line1(line1: str) -> datetime:
    # Extraer la parte del epoch: caracteres 18 a 32 (índices 18 a 32, Python es 0-based)
    epoch_str = line1[18:32].strip()
    
    # Año (2 dígitos)
    year_str = epoch_str[:2]
    year = int(year_str)
    # Ajustar siglo (asumiendo 2000-2099)
    if year < 57:  # estándar NORAD (si es menor que 57, es 2000+year, sino 1900+year)
        year += 2000
    else:
        year += 1900
    
    # Día del año con decimales
    day_of_year_str = epoch_str[2:]
    day_of_year = float(day_of_year_str)
    
    # Día entero y fracción
    day_int = int(day_of_year)
    day_fraction = day_of_year - day_int
    
    # Fecha base 1 de enero del año correspondiente
    base_date = datetime(year, 1, 1)
    
    # Fecha completa sumando días enteros y fracción convertida a segundos
    epoch_datetime = base_date + timedelta(days=day_int - 1, seconds=day_fraction * 86400)
    
    return epoch_datetime