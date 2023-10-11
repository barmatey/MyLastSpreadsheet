from uuid import UUID

from loguru import logger

from src.bus.broker import Broker
from src.bus.eventbus import Queue
from src.spreadsheet.sheet import (
    entity as sheet_entity,
    events as sheet_events,
    repository as sheet_repo,
)
from src.spreadsheet.cell import (
    entity as cell_entity,
    events as cell_events,
)
from src.spreadsheet.sindex import (
    entity as sindex_entity,
    events as sindex_events,
)
from src.spreadsheet.sheet_info import (
    entity as sf_entity,
    events as sf_events,
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
        logger.debug(f'DELETE_SINDEXES')
        sheet_info = sindexes[0].sheet_info.model_copy()
        sindex_key = "rows" if isinstance(sindexes[0], sindex_entity.RowSindex) else "cols"
        filter_by = {"sheet_info": sheet_info, sindex_key: sindexes}
        linked_cells = await self._repo.cell_repo.get_many_by_sheet_filters(**filter_by)
        for cell in linked_cells:
            self._events.append(cell_events.CellDeleted(entity=cell))
        for sindex in sindexes:
            self._events.append(sindex_events.SindexDeleted(entity=sindex))

        if sindex_key == "rows":
            sheet_info.size = (sheet_info.size[0] - len(sindexes), sheet_info.size[1])
        else:
            sheet_info.size = (sheet_info.size[0], sheet_info.size[1] - len(sindexes))
        self._events.append(sf_events.SheetInfoUpdated(old_entity=sindexes[0].sheet_info, new_entity=sheet_info))

    async def get_sheet_by_uuid(self, uuid: UUID) -> sheet_entity.Sheet:
        return await self._repo.get_by_uuid(uuid)
