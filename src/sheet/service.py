import pandas as pd

from src.core import Table
from . import domain


class UpdateDiff:

    def __init__(self, old_sheet: domain.Sheet, new_sheet: domain.Sheet):
        self._old_sheet = old_sheet
        self._new_sheet = new_sheet

        self.appended_rows: set[domain.RowSindex] = set()
        self.deleted_rows: set[domain.RowSindex] = set()
        self.moved_rows: set[domain.RowSindex] = set()

        self.appended_cols: set[domain.ColSindex] = set()
        self.deleted_cols: set[domain.ColSindex] = set()
        self.moved_cols: set[domain.ColSindex] = set()

        self.deleted_cells: set[domain.Cell] = set()
        self.appended_cells: set[domain.Cell] = set()
        self.updated_cells: set[domain.Cell] = set()

    def find_updated_cells(self) -> list[domain.Cell]:
        raise NotImplemented

    def find_moved_rows(self, old_sheet: domain.Sheet, new_sheet: domain.Sheet) -> list[domain.RowSindex]:
        raise NotImplemented

    def find_appended_rows(self, old_sheet: domain.Sheet, new_sheet: domain.Sheet) -> pd.DataFrame:
        raise NotImplemented

    def find_appended_cols(self, old_sheet: domain.Sheet, new_sheet: domain.Sheet) -> pd.DataFrame:
        raise NotImplemented

    def find_deleted_rows(self):
        deleted = {
            key: value
            for key, value in self._old_sheet.row_dict.items()
            if self._new_sheet.row_dict.get(key) is None
        }
        self.deleted_rows = self.deleted_rows.union(deleted.values())
        self.deleted_cells = self.deleted_cells.union(
            self._old_sheet.frame.filter(deleted.keys(), axis=0).values.flatten().tolist())

    def find_deleted_cols(self):
        deleted = {
            key: value
            for key, value in self._old_sheet.col_dict.items()
            if self._new_sheet.col_dict.get(key) is None
        }
        self.deleted_cols = self.deleted_cols.union(deleted.values())
        self.deleted_cells = self.deleted_cells.union(
            self._old_sheet.frame.filter(deleted.keys(), axis=1).values.flatten().tolist()
        )

    def find_updates(self, old_sheet: domain.Sheet, new_sheet: domain.Sheet):
        self.moved_rows = self.find_moved_rows(old_sheet, new_sheet)
        self.deleted_rows = self.find_deleted_rows(old_sheet, new_sheet)
        self.deleted_cols = self.find_deleted_cols(old_sheet, new_sheet)
        self.appended_rows = self.find_appended_rows(old_sheet, new_sheet)
        self.appended_cols = self.find_appended_cols(old_sheet, new_sheet)
