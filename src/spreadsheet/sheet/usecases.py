from uuid import UUID

from src.bus.eventbus import Queue
from src.spreadsheet.cell import (
    entity as cell_entity,
)
from src.spreadsheet.sindex import (
    entity as sindex_entity,
)
from src.spreadsheet.sheet_info import (
    entity as sf_entity,
)
from src.spreadsheet.sheet import (
    entity as sheet_entity,
    events as sheet_events,
)


async def create_sheet(table: list[list[cell_entity.CellValue]]) -> sheet_entity.Sheet:
    size = (len(table), len(table[0])) if len(table) else (0, 0)
    sheet_meta = sf_entity.SheetInfo(size=size)
    row_sindexes = [sindex_entity.RowSindex(sheet_info=sheet_meta, position=i) for i in range(0, size[0])]
    col_sindexes = [sindex_entity.ColSindex(sheet_info=sheet_meta, position=j) for j in range(0, size[1])]
    cells = []
    for i, row in enumerate(table):
        for j, cell_value in enumerate(row):
            cells.append(
                cell_entity.Cell(sheet_info=sheet_meta, row_sindex=row_sindexes[i], col_sindex=col_sindexes[j],
                                 value=cell_value))
    sheet = sheet_entity.Sheet(sheet_info=sheet_meta, rows=row_sindexes, cols=col_sindexes, cells=cells)
    Queue().append(sheet_events.SheetCreated(entity=sheet))
    return sheet


async def get_by_uuid(uuid: UUID) -> sheet_entity.Sheet:
    Queue().append(sheet_events.SheetRequested(uuid=uuid))
