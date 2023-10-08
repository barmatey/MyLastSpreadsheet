from ..cell.entity import CellValue, Cell
from ..cell.repository import CellRepo
from ..sheet_meta.entity import SheetMeta
from ..sheet_meta.repository import SheetMetaRepo
from ..sindex.entity import RowSindex, ColSindex
from ..sindex.repository import SindexRepo
from .entity import Sheet


async def create_sheet(table: list[list[CellValue]],
                       sheet_meta_repo: SheetMetaRepo, sindex_repo: SindexRepo, cell_repo: CellRepo) -> Sheet:
    size = (len(table), len(table[0]))
    sheet_meta = SheetMeta(size=size)
    row_sindexes = [RowSindex(sheet=sheet_meta, position=i) for i, in range(0, size[0])]
    col_sindexes = [ColSindex(sheet=sheet_meta, position=j) for j in range(0, size[1])]
    cells = []
    for i, row in enumerate(table):
        for j, cell_value in enumerate(row):
            cells.append(Cell(sheet=sheet_meta, row_sindex=row_sindexes[i], col_sindex=col_sindexes[j], value=cell_value))

    await sheet_meta_repo.add(sheet_meta)
    await sindex_repo.add_many(row_sindexes)
    await sindex_repo.add_many(col_sindexes)
    await cell_repo.add_many(cells)
    return Sheet(sheet_meta=sheet_meta, rows=row_sindexes, cols=col_sindexes, cells=cells)
