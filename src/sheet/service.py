import pandas as pd

from src.core import Table
from . import domain


def convert_to_simple_frame(sheet: pd.DataFrame) -> pd.DataFrame:
    rows = [x.position for x in sheet.index]
    cols = [x.position for x in sheet.index]
    data = sheet.apply(lambda x: x.apply(lambda y: y.value)).values
    return pd.DataFrame(data, index=rows, columns=cols)


def create_sheet_from_table(table: Table[domain.CellValue], rows=None, cols=None) -> domain.Sheet:
    if rows is None:
        rows = [domain.RowSindex(position=i) for i in range(0, len(table))]
    else:
        rows = [x.model_copy() for x in rows]
    if cols is None:
        cols = [domain.ColSindex(position=j) for j in range(0, len(table[0]))]
    else:
        cols = [x.model_copy() for x in cols]
    values = []
    for i, row in enumerate(table):
        if len(row) != len(cols):
            raise Exception
        cells = [domain.Cell(value=value, row=rows[i], col=cols[j]) for j, value in enumerate(row)]
        values.append(cells)

    if len(rows) != len(values):
        raise Exception
    if len(cols) != len(values[0]):
        raise Exception

    return domain.Sheet(values, index=rows, columns=cols)


class UpdateDiff:

    def __init__(self):
        self.appended_rows = None
        self.appended_cols = None
        self.deleted_cols = None
        self.deleted_rows = None
        self.moved_rows = None

    def find_updated_cells(self, old_sheet: pd.DataFrame, new_sheet: pd.DataFrame) -> list[domain.Cell]:
        diff = old_sheet.compare(new_sheet, align_axis='index')

        updated_cells: list[domain.Cell] = []
        for col in diff.columns:
            temp = diff[col].dropna()
            for i in range(0, len(temp.index), 2):
                cell = domain.Cell(
                    id=temp.iloc[i].id,
                    value=temp.iloc[i + 1].value,
                    row=temp.iloc[i].row,
                    col=temp.iloc[i].col,
                    background=temp.iloc[i].background,
                )
                updated_cells.append(cell)
        return updated_cells

    def find_moved_rows(self, old_sheet: pd.DataFrame, new_sheet: pd.DataFrame) -> list[domain.RowSindex]:
        old_rows = {x.id: x for x in old_sheet.index}
        new_rows = {x.id: x for x in new_sheet.index}

        moved = []
        for row_id in new_rows:
            new = new_rows[row_id]
            old = old_rows.get(row_id)
            if old is not None:
                if new.position != old.position:
                    moved.append(domain.RowSindex(
                        id=old.id,
                        is_freeze=old.is_freeze,
                        is_readonly=old.is_readonly,
                        position=new.position,
                        size=old.size,
                    ))
        return moved

    def find_appended_rows(self, old_sheet: pd.DataFrame, new_sheet: pd.DataFrame) -> pd.DataFrame:
        return self.find_deleted_rows(new_sheet, old_sheet)

    def find_appended_cols(self, old_sheet: pd.DataFrame, new_sheet: pd.DataFrame) -> pd.DataFrame:
        return self.find_deleted_cols(new_sheet, old_sheet)

    def find_deleted_rows(self, old_sheet: pd.DataFrame, new_sheet: pd.DataFrame) -> pd.DataFrame:
        old = set(old_sheet.index)
        new = set(new_sheet.index)
        deleted_rows = old.difference(new)
        deleted_rows_and_cells = old_sheet.filter(deleted_rows, axis=0)
        return deleted_rows_and_cells

    def find_deleted_cols(self, old_sheet: pd.DataFrame, new_sheet: pd.DataFrame) -> pd.DataFrame:
        old = set(old_sheet.columns)
        new = set(new_sheet.columns)
        deleted_cols = old.difference(new)
        deleted_cols_and_cells = old_sheet.filter(deleted_cols, axis=1)
        return deleted_cols_and_cells

    def find_updates(self, old_sheet: pd.DataFrame, new_sheet: pd.DataFrame):
        self.moved_rows = self.find_moved_rows(old_sheet, new_sheet)
        self.deleted_rows = self.find_deleted_rows(old_sheet, new_sheet)
        self.deleted_cols = self.find_deleted_cols(old_sheet, new_sheet)
        self.appended_rows = self.find_appended_rows(old_sheet, new_sheet)
        self.appended_cols = self.find_appended_cols(old_sheet, new_sheet)
