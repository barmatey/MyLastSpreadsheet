from uuid import UUID, uuid4
from pydantic import Field

from src.bus.events import Created, Updated, Deleted, Subscribed, Unsubscribed, Event
from ..cell.entity import CellValue
from .entity import SheetMeta


class SheetCreated(Created[SheetMeta]):
    pass


class SheetSizeUpdated(Updated[SheetMeta]):
    pass


class SheetDeleted(Deleted[SheetMeta]):
    pass


class SheetSubscribed(Subscribed):
    pass


class SheetUnsubscribed(Unsubscribed):
    pass


class SheetRowsAppended(Event):
    table: list[list[CellValue]]
    uuid: UUID = Field(default_factory=uuid4)
