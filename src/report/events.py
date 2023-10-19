from uuid import UUID, uuid4

from pydantic import Field

from src.base.eventbus import Event
from . import domain


class WiresAppended(Event):
    source: domain.SourceInfo
    wires: list[domain.Wire]
    id: UUID = Field(default_factory=uuid4)
