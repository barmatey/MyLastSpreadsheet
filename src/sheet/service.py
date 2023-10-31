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

    def find_moved_rows(self):
        for key, new_value in self._new_sheet.row_dict.items():
            old_value = self._old_sheet.row_dict.get(key)
            if old_value:
                if old_value.position != new_value.position:
                    self.moved_rows.add(new_value)

    def find_moved_cols(self):
        for key, new_value in self._new_sheet.col_dict.items():
            old_value = self._old_sheet.col_dict.get(key)
            if old_value:
                if old_value.position != new_value.position:
                    self.moved_cols.add(new_value)

    def find_appended_rows(self):
        appended = {
            key: value
            for key, value in self._new_sheet.row_dict.items()
            if self._old_sheet.row_dict.get(key) is None
        }
        self.appended_rows = self.appended_rows.union(appended.values())
        self.appended_cells = self.appended_cells.union(
            self._new_sheet.frame.filter(appended.keys(), axis=0).values.flatten().tolist()
        )

    def find_appended_cols(self):
        appended = {
            key: value
            for key, value in self._new_sheet.col_dict.items()
            if self._old_sheet.col_dict.get(key) is None
        }
        self.appended_cols = self.appended_cols.union(appended.values())
        self.appended_cells = self.appended_cells.union(
            self._new_sheet.frame.filter(appended.keys(), axis=1).values.flatten().tolist()
        )

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
        raise NotImplemented
