from src.bus.events import Updated
from . import (
    entity as sf_entity,
)


class SheetInfoUpdated(Updated[sf_entity.SheetInfo]):
    pass
