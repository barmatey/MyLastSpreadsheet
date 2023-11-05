from uuid import UUID

from pydantic import BaseModel

from .. import domain
from . import helpers
from ...core import Table


class SindexSchema(BaseModel):
    id: UUID
    position: bool
    scroll: bool
    size: bool
    is_readonly: bool
    is_freeze: bool
    sheet_id: UUID

    @classmethod
    def from_sindex(cls, sindex: domain.Sindex) -> 'SindexSchema':
        return cls(
            id=sindex.id,
            position=sindex.position,
            size=sindex.size,
            is_readonly=sindex.is_readonly,
            is_freeze=sindex.is_freeze,
            scroll=0,
            sheet_id=sindex.sheet_id,
        )


class CellSchema(BaseModel):
    id: UUID
    value: str
    dtype: domain.CellDtype
    is_readonly: bool
    is_filtred: bool
    is_index: bool
    background: str
    text_align: str
    row_id: UUID
    col_id: UUID
    sheet_id: UUID

    @classmethod
    def from_cell(cls, cell: domain.Cell) -> 'CellSchema':
        return cls(
            id=cell.id,
            value=str(cell.value),
            dtype=helpers.get_dtype(cell.value),
            is_readonly=False,
            is_filtred=True,
            is_index=False,
            background=cell.background,
            text_align="LEFT",
            row_id=cell.row.id,
            col_id=cell.col.id,
            sheet_id=cell.sheet_id,
        )


class SheetSchema(BaseModel):
    id: UUID
    rows: list[SindexSchema]
    cols: list[SindexSchema]
    table: Table[CellSchema]

    @classmethod
    def from_sheet(cls, sheet: domain.Sheet) -> 'SheetSchema':
        table = []
        for row in sheet.table:
            table.append([])
            for cell in row:
                table[-1].append(CellSchema.from_cell(cell))

        return cls(
            id=sheet.sf.id,
            rows=[SindexSchema.from_sindex(x) for x in sheet.rows],
            cols=[SindexSchema.from_sindex(x) for x in sheet.cols],
            table=table,
        )
