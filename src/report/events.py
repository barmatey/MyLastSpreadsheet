from uuid import UUID, uuid4

from pydantic import Field

from src.base.eventbus import Event
from . import domain


class WiresAppended(Event):
    source_info: domain.SourceInfo
    wires: list[domain.Wire]
    id: UUID = Field(default_factory=uuid4)


class WiresDeleted(Event):
    source_info: domain.SourceInfo
    wires: list[domain.Wire]
    id: UUID = Field(default_factory=uuid4)


class WiresUpdated(Event):
    source_info: domain.SourceInfo
    old_values: list[domain.Wire]
    new_values: list[domain.Wire]
    id: UUID = Field(default_factory=uuid4)
