from uuid import UUID

from loguru import logger

from src.bus.broker import Broker
from src.bus.eventbus import Queue
from src.spreadsheet.sheet import (
    entity as sheet_entity,
    events as sheet_events,
    subscriber as sheet_subscriber,
    repository as sheet_repo,
)
from src.spreadsheet.cell import (
    entity as cell_entity,
    events as cell_events,
    services as cell_services,
)
from src.spreadsheet.sindex import (
    entity as sindex_entity,
    events as sindex_events,
    services as sindex_services,
)
from src.spreadsheet.sheet_info import (
    entity as sf_entity,
    services as sf_services,
)


class SheetHandler:
    def __init__(self, repo: sheet_repo.SheetRepo, broker: Broker):
        self._repo = repo
        self._broker = broker

    async def handle_sheet_created(self, event: sheet_events.SheetCreated):
        raise NotImplemented


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

        await self._repo.add(sheet)
        return sheet

    async def delete_sindexes(self, sindexes: list[sindex_entity.Sindex]):
        logger.debug(f'DELETE_SINDEXES')
        sheet_info = sindexes[0].sheet_info
        sindex_key = "rows" if isinstance(sindexes[0], sindex_entity.RowSindex) else "cols"

        filter_by = {"sheet_info": sheet_info, sindex_key: sindexes}
        linked_cells = await self._repo.cell_repo.get_many_by_sheet_filters(**filter_by)
        await self._repo.cell_repo.remove_many(linked_cells)
        for cell in linked_cells:
            self._events.append(cell_events.CellDeleted(entity=cell))

        await self._repo.sindex_repo.remove_many(sindexes)
        for sindex in sindexes:
            self._events.append(sindex_events.SindexDeleted(entity=sindex))

        if sindex_key == "rows":
            sheet_info.size = (sheet_info.size[0] - len(sindexes), sheet_info.size[1])
        else:
            sheet_info.size = (sheet_info.size[0], sheet_info.size[1] - len(sindexes))
        await self._repo.sheet_info_repo.update(sheet_info)

    async def get_sheet_by_uuid(self, uuid: UUID) -> sheet_entity.Sheet:
        return await self._repo.get_by_uuid(uuid)


class SheetSelfSubscriber(sheet_subscriber.SheetSubscriber):
    def __init__(self, entity: sheet_entity.Sheet, repo: sheet_repo.SheetRepo, queue: Queue):
        self._entity = entity
        self._events = queue
        self._repo = repo

    @property
    def entity(self):
        return self._entity

    async def follow_sheet(self, pub: sheet_entity.Sheet):
        if self._entity.sheet_info.size != (0, 0):
            raise ValueError
        sindex_service = sindex_services.SindexService(self._repo, self._events)
        cell_service = cell_services.CellService(self._repo, self._events)

        rows = []
        for parent_row in pub.rows:
            child_row = sindex_entity.RowSindex(position=parent_row.position, sheet_info=self._entity.sheet_info)
            await sindex_service.create_sindex(child_row)
            await sindex_service.subscribe_sindex([parent_row], child_row)
            rows.append(child_row)

        cols = []
        for parent_col in pub.cols:
            child_col = sindex_entity.ColSindex(position=parent_col.position, sheet_info=self._entity.sheet_info)
            await sindex_service.create_sindex(child_col)
            await sindex_service.subscribe_sindex([parent_col], child_col)
            cols.append(child_col)

        for i, row in enumerate(rows):
            for j, col in enumerate(cols):
                index = i * pub.sheet_info.size[1] + j
                child_cell = cell_entity.Cell(sheet_info=self._entity.sheet_info, row_sindex=row, col_sindex=col,
                                              value=pub.cells[index].value)
                await cell_service.create_cell(child_cell)
                await cell_service.subscribe_cell([pub.cells[index]], child_cell)

        self._entity.sheet_info.size = pub.sheet_info.size
        await sf_services.SheetInfoService(self._repo, self._events).update_sheet_info(self._entity.sheet_info)

    async def unfollow_sheet(self, pub: sheet_entity.Sheet):
        raise NotImplemented

    async def on_rows_appended(self, table: list[list[cell_entity.CellValue]]):
        raise NotImplemented

    async def on_sheet_deleted(self):
        raise NotImplemented
