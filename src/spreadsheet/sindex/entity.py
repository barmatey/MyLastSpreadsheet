from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from ..sheet.entity import Sheet


class Sindex(BaseModel):
    sheet: Sheet
    position: int
    uuid: UUID = Field(default_factory=uuid4)


class RowSindex(Sindex):
    pass


class ColSindex(Sindex):
    pass
