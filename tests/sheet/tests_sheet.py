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
    cols = [domain.ColSindex(position=0), domain.ColSindex(position=1)]
    rows = [domain.RowSindex(position=0), domain.RowSindex(position=1), domain.RowSindex(position=2)]
    sheet1 = create_sheet_from_table([[1, 2], [3, 4], [5, 6]], rows, cols)

    print()
    print(sheet1.columns[0], type(sheet1.columns[0]))
    print(cols[0], type(cols[0]))

    sheet1.drop(cols[0], axis=1)
