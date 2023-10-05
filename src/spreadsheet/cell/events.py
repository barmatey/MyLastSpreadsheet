from src.bus.events import Created, Updated, Deleted, Subscribed, Unsubscribed
from src.spreadsheet.cell.entity import Cell


class CellCreated(Created[Cell]):
    pass


class CellUpdated(Updated[Cell]):
    pass


class CellDeleted(Deleted[Cell]):
    pass


class CellSubscribed(Subscribed):
    pass


class CellUnsubscribed(Unsubscribed):
    pass
