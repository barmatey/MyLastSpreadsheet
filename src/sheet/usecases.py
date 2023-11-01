import pandas as pd

from . import schema


class SheetDifference:
    def __init__(self, old_sheet: schema.Sheet, new_sheet: schema.Sheet):
        self._old_sheet = old_sheet
        self._new_sheet = new_sheet

        self.appended_rows: set[schema.RowSindex] = set()
        self.deleted_rows: set[schema.RowSindex] = set()
        self.moved_rows: set[schema.RowSindex] = set()

        self.appended_cols: set[schema.ColSindex] = set()
        self.deleted_cols: set[schema.ColSindex] = set()
        self.moved_cols: set[schema.ColSindex] = set()

        self.deleted_cells: set[schema.Cell] = set()
        self.appended_cells: set[schema.Cell] = set()
        self.updated_cells: set[schema.Cell] = set()

    def find_updated_cells(self):
        common_rows = list(set(self._old_sheet.row_dict.keys()).intersection(self._new_sheet.row_dict.keys()))
        common_cols = list(set(self._old_sheet.col_dict.keys()).intersection(self._new_sheet.col_dict.keys()))
        old = self._old_sheet.frame.loc[common_rows, common_cols]
        new = self._new_sheet.frame.loc[common_rows, common_cols]
        diff: pd.DataFrame = old.compare(new, align_axis=0)
        for col in diff.columns:
            temp = diff[col].dropna()
            for i in range(0, len(temp), 2):
                self.updated_cells.add(temp[i + 1])

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

    def find_updates(self):
        self.find_appended_rows()
        self.find_deleted_rows()
        self.find_moved_rows()

        self.find_appended_cols()
        self.find_deleted_cols()
        self.find_moved_cols()

        self.find_updated_cells()
