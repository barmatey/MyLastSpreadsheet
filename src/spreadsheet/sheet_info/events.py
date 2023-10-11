from src.bus.events import Updated
from . import (
    entity as sf_entity,
)


class SheetInfoUpdated(Updated[sf_entity.SheetInfo]):
    pass

    def __repr__(self):
        return f"SheetInfoUpdated(old={self.old_entity}, new={self.new_entity})"

    def __str__(self):
        return self.__repr__()
