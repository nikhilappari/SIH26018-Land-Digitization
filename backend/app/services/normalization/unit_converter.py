from typing import Tuple

# Conversion factors to standard unit (Acres)
UNIT_TO_ACRES = {
    "acres": 1.0,
    "acre": 1.0,
    "guntas": 0.025,
    "gunta": 0.025,
    "guntha": 0.025,
    "hectares": 2.47105,
    "hectare": 2.47105,
    "sq yards": 0.000206612,
    "sq yard": 0.000206612,
    "cent": 0.01,
    "cents": 0.01,
    "bigha": 0.625, # standard benchmark average
    "biswa": 0.03125
}

def convert_area_unit(value: float, from_unit: str, to_unit: str = "Acres") -> float:
    """
    Converts Indian regional area measurement units to standard unit (default Acres).
    """
    if value is None or value <= 0:
        return 0.0
    from_key = (from_unit or "Acres").lower().strip()
    to_key = (to_unit or "Acres").lower().strip()
    
    # Convert from source unit to Acres
    factor_to_acres = UNIT_TO_ACRES.get(from_key, 1.0)
    value_in_acres = value * factor_to_acres
    
    # Convert from Acres to target unit
    factor_from_acres = 1.0 / UNIT_TO_ACRES.get(to_key, 1.0)
    return round(value_in_acres * factor_from_acres, 4)
