from uuid import UUID, uuid4

from pydantic import Field

from src.base.eventbus import Event
from . import domain


class WiresAppended(Event):
    source_info: domain.SourceInfo
    wires: list[domain.Wire]
    id: UUID = Field(default_factory=uuid4)


class GroupRowsAppended(Event):
    group_info: domain.Group
    rows: list[list[domain.CellValue]]
    id: UUID = Field(default_factory=uuid4)
