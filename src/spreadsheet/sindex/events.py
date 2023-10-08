from src.bus.events import Deleted, Updated, Subscribed


class SindexUpdated(Updated):
    pass


class SindexDeleted(Deleted):
    pass


class SindexSubscribed(Subscribed):
    pass
