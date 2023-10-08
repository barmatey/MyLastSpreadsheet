from uuid import UUID

from src.spreadsheet.cell.entity import CellValue, Cell
from src.spreadsheet.cell.repository import CellRepo
from src.spreadsheet.sheet_meta.entity import SheetMeta
from src.spreadsheet.sheet_meta.repository import SheetRepo
from src.spreadsheet.sindex.entity import RowSindex, ColSindex
from src.spreadsheet.sindex.repository import SindexRepo


async def create_sheet(table: list[list[CellValue]],
                       sheet_repo: SheetRepo, sindex_repo: SindexRepo, cell_repo: CellRepo) -> SheetMeta:
    size = (len(table), len(table[0]))
    sheet = SheetMeta(size=size)
    row_sindexes = [RowSindex(sheet=sheet, position=i) for i, in range(0, size[0])]
    col_sindexes = [ColSindex(sheet=sheet, position=j) for j in range(0, size[1])]
    cells = []
    for i, row in enumerate(table):
        for j, cell_value in enumerate(row):
            cells.append(Cell(sheet=sheet, row_sindex=row_sindexes[i], col_sindex=col_sindexes[j], value=cell_value))

    await sheet_repo.add(sheet)
    await sindex_repo.add_many(row_sindexes)
    await sindex_repo.add_many(col_sindexes)
    await cell_repo.add_many(cells)
    return sheet


async def get_sheet_by_uuid(uuid: UUID, repo: SheetRepo) -> SheetMeta:
    return await repo.get_one_by_uuid(uuid)


async def update_sheet(sheet: SheetMeta, repo: SheetRepo):
    await repo.update(sheet)
