from uuid import uuid4

import pandas as pd
from src.sheet.service import *


def test_sum_two_sheets():
    sheet1 = domain.Sheet.from_table([[1, 1], [1, 1]])
    actual = sheet1 + sheet1

    expected = f"{[[2, 2], [2, 2]]}"
    actual = f"{actual.to_table()}"
    assert actual == expected

    expected = f"{[[1, 1], [1, 1]]}"
    actual = f"{sheet1.to_table()}"
    assert actual == expected


def test_drop():
    sheet = domain.Sheet.from_table([[1, 2], [3, 4], [5, 6]])
    actual = sheet.drop(sheet.frame.index[1], axis=0).reindex_rows().drop(sheet.frame.columns[0], axis=1).reindex_cols()
    assert len(actual.frame.index) == 2
    assert len(actual.frame.columns) == 1
    for i, row in enumerate(actual.rows):
        assert row.position == i
    for j, col in enumerate(actual.cols):
        assert col.position == j


def test_update_diff():
    sheet1 = domain.Sheet.from_table([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    sheet2 = sheet1.copy().drop(sheet1.rows[1].id, axis=0).drop(sheet1.cols[0].id, axis=1)

    diff = UpdateDiff(sheet1, sheet2)
    diff.find_deleted_rows()
    diff.find_deleted_cols()

    print()
    print("DELETED_ROWS: ", diff.deleted_rows)
    print("DELETED COLS: ", diff.deleted_cols)
    print("DELETED CELLS: ", diff.deleted_cells)
    print("")
