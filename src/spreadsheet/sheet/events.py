from uuid import UUID, uuid4
from pydantic import Field

from src.bus.events import Created, Updated, Deleted, Subscribed, Unsubscribed, Event, Requested
from src.spreadsheet.cell.entity import CellValue
from src.spreadsheet.sheet.entity import Sheet


class SheetCreated(Created[Sheet]):
    pass


class SheetRequested(Requested):
    pass


class SheetSizeUpdated(Updated[Sheet]):
    pass


class SheetDeleted(Deleted[Sheet]):
    pass


class SheetSubscribed(Subscribed):
    pass


class SheetUnsubscribed(Unsubscribed):
    pass


class SheetRowsAppended(Event):
    table: list[list[CellValue]]
    uuid: UUID = Field(default_factory=uuid4)
