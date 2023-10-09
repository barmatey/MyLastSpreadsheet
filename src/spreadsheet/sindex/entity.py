from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from ..sheet_info.entity import SheetInfo

SindexDirection = Literal["ROW", "COL"]


class Sindex(BaseModel):
    sheet_info: SheetInfo
    position: int
    uuid: UUID = Field(default_factory=uuid4)

    def __str__(self):
        return f"{self.__class__.__name__}(position={self.position})"

    def __repr__(self):
        return f"{self.__class__.__name__}(position={self.position})"

    def __hash__(self):
        return self.uuid.__hash__()

    def __eq__(self, other: 'Sindex'):
        return all([
            self.sheet_info == other.sheet_info,
            self.position == other.position,
            self.uuid == other.uuid,
        ])


class RowSindex(Sindex):
    pass


class ColSindex(Sindex):
    pass
