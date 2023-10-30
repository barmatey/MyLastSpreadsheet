import pandas as pd

from src.sheet import domain
from src.sheet.service import SheetService


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
    sheet1 = SheetService.from_table([[0, 0, ], [0, 0]], rows, cols)
    sheet2 = SheetService.from_table([[1, 2], [3, 4]], rows, cols)
    sheet3 = sheet1 + sheet2

    expected = f"{[[1 ,2], [3, 4]]}"
    actual = f"{sheet3.to_simple_frame().values.tolist()}"
    assert actual == expected
