from uuid import UUID, uuid4
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field

from src.bus.events import Created, Updated, Deleted, Subscribed, Unsubscribed


def size_factory():
    return 0, 0


class Sheet(BaseModel):
    size: tuple[int, int] = Field(default_factory=size_factory)
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
