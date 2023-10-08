from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from ..sheet_info.entity import SheetMeta

SindexDirection = Literal["ROW", "COL"]


class Sindex(BaseModel):
    sheet: SheetMeta
    position: int
    uuid: UUID = Field(default_factory=uuid4)

    def __str__(self):
        return f"{self.__class__.__name__}(position={self.position})"

    def __repr__(self):
        return f"{self.__class__.__name__}(position={self.position})"


class RowSindex(Sindex):
    pass


class ColSindex(Sindex):
    pass
