from src.bus.events import Deleted, Updated, Subscribed, Created
from src.spreadsheet.sindex.entity import Sindex


class SindexCreated(Created[Sindex]):
    pass


class SindexUpdated(Updated[Sindex]):
    pass


class SindexDeleted(Deleted[Sindex]):
    pass


class SindexSubscribed(Subscribed):
    pass
