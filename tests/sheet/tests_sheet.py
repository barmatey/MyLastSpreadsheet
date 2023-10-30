import pandas as pd
from src.sheet.service import *


def test_from_table_constructor():
    sheet = SheetService.from_table([
        [1, 2],
        [3, 4]
    ])
    print()
    print(sheet)


def test_sum_two_sheets():
    rows = [domain.RowSindex(position=0), domain.RowSindex(position=1)]
    cols = [domain.ColSindex(position=0), domain.ColSindex(position=1)]
    sheet1 = create_sheet_from_table([[0, 0, ], [0, 0]], rows, cols)
    sheet2 = create_sheet_from_table([[1, 2], [3, 4]], rows, cols)
    sheet3 = sheet1 + sheet2

    expected = f"{[[1 ,2], [3, 4]]}"
    actual = f"{convert_to_simple_frame(sheet3).values.tolist()}"
    assert actual == expected


def test_update_diff():
    cols = [domain.ColSindex(position=0), domain.ColSindex(position=1)]
    rows = [domain.RowSindex(position=0), domain.RowSindex(position=1)]
    sheet1 = create_sheet_from_table([[0, 0, ], [0, 0]], rows, cols)
    sheet2 = create_sheet_from_table([[1, 2], [3, 4]], rows, cols)
    sheet2reversed = create_sheet_from_table([[3, 4], [1, 2]], reversed(rows), cols)
    sheet3 = create_sheet_from_table([[1, 2]], rows[:1], cols)

    diff = UpdateDiff().find_moved_rows(sheet2, sheet2reversed)
    print()
    print(diff)
