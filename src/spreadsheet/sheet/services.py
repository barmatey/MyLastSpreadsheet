from uuid import UUID

from src.bus.broker import Broker
from src.bus.eventbus import Queue
from src.spreadsheet.sheet import (
    entity as sheet_entity,
    events as sheet_events,
    repository as sheet_repo,
)
from src.spreadsheet.cell import (
    entity as cell_entity,
)
from src.spreadsheet.sindex import (
    entity as sindex_entity,
)
from src.spreadsheet.sheet_info import (
    entity as sf_entity,
)


class SheetHandler:
    def __init__(self, repo: sheet_repo.SheetRepo, broker: Broker):
        self._repo = repo
        self._broker = broker

    async def handle_sheet_created(self, event: sheet_events.SheetCreated):
        await self._repo.add(event.entity)


class SheetService:
    def __init__(self, repo: sheet_repo.SheetRepo, queue: Queue):
        self._repo = repo
        self._events = queue

    async def create_sheet(self, table: list[list[cell_entity.CellValue]]) -> sheet_entity.Sheet:
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
        self._events.append(sheet_events.SheetCreated(entity=sheet))
        return sheet

    async def delete_sindexes(self, sindexes: list[sindex_entity.Sindex]):
        raise NotImplemented

    async def get_sheet_by_uuid(self, uuid: UUID) -> sheet_entity.Sheet:
        return await self._repo.get_by_uuid(uuid)
