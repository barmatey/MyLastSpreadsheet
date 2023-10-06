from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from ..sheet.entity import Sheet

SindexDirection = Literal["ROW", "COL"]


class Sindex(BaseModel):
    sheet: Sheet
    direction: SindexDirection
    position: int
    uuid: UUID = Field(default_factory=uuid4)


class RowSindex(Sindex):
    pass


class ColSindex(Sindex):
    pass
