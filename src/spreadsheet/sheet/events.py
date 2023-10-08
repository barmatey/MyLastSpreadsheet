from uuid import UUID, uuid4
from pydantic import Field

from src.bus.events import Created, Updated, Deleted, Subscribed, Unsubscribed, Event
from src.spreadsheet.cell.entity import CellValue
from src.spreadsheet.sheet_info.entity import SheetInfo


class SheetCreated(Created[SheetInfo]):
    pass


class SheetSizeUpdated(Updated[SheetInfo]):
    pass


class SheetDeleted(Deleted[SheetInfo]):
    pass


class SheetSubscribed(Subscribed):
    pass


class SheetUnsubscribed(Unsubscribed):
    pass


class SheetRowsAppended(Event):
    table: list[list[CellValue]]
    uuid: UUID = Field(default_factory=uuid4)
