from abc import ABC, abstractmethod
from uuid import UUID, uuid4

from pydantic import Field

from src.bus.events import Created, Updated, Deleted, Subscribed, Unsubscribed, Event

from ..sheet.domain import Sheet


class SheetCreated(Created[Sheet]):
    pass


class SheetUpdated(Updated[Sheet]):
    pass


class SheetDeleted(Deleted[Sheet]):
    pass


class SheetSubscribed(Subscribed):
    pass


class SheetUnsubscribed(Unsubscribed):
    pass


class SheetRowsAppended(Event):
    uuid: UUID = Field(default_factory=uuid4)


class SheetSubscriber(ABC):
    @abstractmethod
    def follow_sheet(self, pub: Sheet):
        raise NotImplemented

    @abstractmethod
    def unfollow_sheet(self, pub: Sheet):
        raise NotImplemented

    @abstractmethod
    def on_rows_appended(self):
        raise NotImplemented

    @abstractmethod
    def on_sheet_deleted(self):
        raise NotImplemented
