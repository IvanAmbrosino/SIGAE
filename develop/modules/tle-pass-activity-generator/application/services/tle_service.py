from domain.entities.tle_data import TleData
from datetime import datetime, timedelta
import uuid
import re

from domain.ports.tle_repository import TleRepository

def process_and_save_tle(tle_repository: TleRepository, tle_message: dict) -> TleData:
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
    
    tle_repository.save_tle_data(tle_data)
    return tle_data

def get_norad_id(line1: str) -> str:
    match = re.match(r"1\s+(\d{5})U", line1)
    if match:
        return match.group(1)
    raise ValueError("Formato de TLE inválido")


def parse_epoch_from_line1(line1: str) -> datetime:
    epoch_str = line1[18:32].strip()
    year = int(epoch_str[:2])
    year += 2000 if year < 57 else 1900
    day_of_year = float(epoch_str[2:])
    day_int = int(day_of_year)
    day_fraction = day_of_year - day_int
    base_date = datetime(year, 1, 1)
    return base_date + timedelta(days=day_int - 1, seconds=day_fraction * 86400)
