import pandas as pd

from . import service


class UpdateSheet:
    def __init__(self, repo):
        self._repo = repo
        self._old_sheet = None
        self._new_sheet = None

    def load_data(self, old_sheet: pd.DataFrame, new_sheet: pd.DataFrame):
        self._old_sheet = old_sheet
        self._new_sheet = new_sheet

    def execute(self):
        diff = service.UpdateDiff()
        deleted_rows = diff.find_deleted_rows(self._old_sheet, self._new_sheet)



