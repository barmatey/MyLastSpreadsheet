from datetime import datetime

from .. import domain


def get_value(value: str, dtype: domain.CellDtype) -> domain.CellValue:
    if dtype == "string" and value == "None":
        return None
    if dtype == "string":
        return value
    if dtype == "int":
        return int(value)
    if dtype == "float":
        return float(value)
    if dtype == "bool" and value == "True":
        return True
    if dtype == "bool" and value == "False":
        return False
    if dtype == "datetime":
        return datetime.fromisoformat(value)
    raise TypeError(f"{value}, {dtype}")


def get_dtype(value: domain.CellValue) -> domain.CellDtype:
    if value is None:
        return "string"
    if isinstance(value, int):
        return "int"
    if isinstance(value, str):
        return "string"
    if isinstance(value, float):
        return "float"
    if isinstance(value, datetime):
        return "datetime"
    if isinstance(value, bool):
        return "bool"
    raise TypeError
