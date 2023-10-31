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
    sheet2 = (
        sheet1
        .drop(sheet1.rows[1].id, axis=0)
        .drop(sheet1.cols[0].id, axis=1)
    )
    new_rows = domain.Sheet.from_table([[77, 88]], cols=sheet2.cols)
    sheet2 = sheet2.concat(new_rows)

    new_cols = domain.Sheet.from_table([[22, 22]], rows=sheet2.rows)
    print()
    print(new_cols)
    sheet2 = sheet2.concat(new_cols, axis=1)


    diff = UpdateDiff(sheet1, sheet2)
    diff.find_deleted_rows()
    diff.find_deleted_cols()
    diff.find_moved_rows()
    diff.find_moved_cols()
    diff.find_appended_rows()
    diff.find_appended_cols()

    print()
    print(f"DELETED_ROWS ({len(diff.deleted_rows)}): ", diff.deleted_rows)
    print(f"DELETED COLS ({len(diff.moved_cols)}): ", diff.deleted_cols)
    print(f"DELETED CELLS ({len(diff.deleted_cells)}): ", diff.deleted_cells)
    print(f"MOVED ROWS ({len(diff.moved_rows)}): ", diff.moved_rows)
    print(f"MOVED COLS ({len(diff.moved_cols)}): ", diff.moved_cols)
    print(f"APPENDED ROWS ({len(diff.appended_rows)}): ", diff.appended_rows)
    print(f"APPENDED COLS ({len(diff.appended_cols)}): ", diff.appended_cols)
    print(f"APPENDED CELLS ({len(diff.appended_cells)}): ", diff.appended_cells)
