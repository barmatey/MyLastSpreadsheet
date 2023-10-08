from abc import ABC, abstractmethod
from ..cell.entity import CellValue
from ..sheet_info.entity import SheetInfo


class SheetSubscriber(ABC):
    @abstractmethod
    def follow_sheet(self, pub: SheetInfo):
        raise NotImplemented

    @abstractmethod
    def unfollow_sheet(self, pub: SheetInfo):
        raise NotImplemented

    @abstractmethod
    def on_rows_appended(self, table: list[list[CellValue]]):
        raise NotImplemented

    @abstractmethod
    def on_sheet_deleted(self):
        raise NotImplemented


class SheetSelfSubscriber(SheetSubscriber):
    def follow_sheet(self, pub: SheetInfo):
        pass

    def unfollow_sheet(self, pub: SheetInfo):
        pass

    def on_rows_appended(self, table: list[list[CellValue]]):
        pass

    def on_sheet_deleted(self):
        pass
