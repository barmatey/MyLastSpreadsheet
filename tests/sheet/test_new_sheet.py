from src.sheet import schema, usecases
from src.helpers.arrays import flatten


def test_drop():
    sheet: schema.Sheet = schema.Sheet.from_table([[1, 2], [3, 4], [5, 6]])
    actual = sheet.drop(sheet.rows[1].id, axis=0).drop(sheet.cols[0].id, axis=1)
    assert len(actual.rows) == 2
    assert len(actual.cols) == 1
    for i, row in enumerate(actual.rows):
        assert row.position == i
    for j, col in enumerate(actual.cols):
        assert col.position == j


def test_resize_sheet():
    sheet1 = schema.Sheet.from_table([
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
    ])
    actual = sheet1.resize(2, 2)
    assert len(actual.rows) == 2
    assert len(actual.cols) == 2
    assert len(actual.table) == 2
    assert len(actual.table[0]) == len(actual.table[1]) == 2

    actual = sheet1.resize(5, 5)
    assert len(actual.rows) == 5
    assert len(actual.cols) == 5
    assert len(actual.table) == 5
    for row in actual.table:
        assert len(row) == 5


def test_replace_cell_values():
    sheet1 = schema.Sheet.from_table([
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
    ])
    actual = sheet1.replace_cell_values([
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
    ])
    assert len(actual.rows) == len(sheet1.rows)
    assert len(actual.cols) == len(sheet1.cols)
    for lhs, rhs in zip(actual.rows, sheet1.rows):
        assert lhs.id == rhs.id
    for lhs, rhs in zip(actual.cols, sheet1.cols):
        assert lhs.id == rhs.id
    for lhs, rhs in zip(flatten(actual.table), flatten(sheet1.table)):
        assert lhs.id == rhs.id
    for i, cell in enumerate(flatten(actual.table), start=1):
        assert cell.value == i


def test_concat():
    sheet1 = schema.Sheet.from_table([
        [1, 2, 3, ],
        [4, 5, 6],
    ])
    sheet2 = schema.Sheet.from_table([
        [7, 8, 9]
    ])
    sheet3 = schema.Sheet.from_table([
        [11],
        [22],
    ])

    actual = schema.concat(sheet1, sheet2, axis=0)
    assert len(actual.rows) == 3
    assert len(actual.cols) == 3
    for i, row in enumerate(actual.rows):
        assert row.position == i
    for j, col in enumerate(actual.cols):
        assert col.position == j
    for i, cell in enumerate(flatten(actual.table), start=1):
        assert cell.value == i

    actual = schema.concat(sheet1, sheet3, axis=1)
    assert len(actual.rows) == 2
    assert len(actual.cols) == 4
    for i, row in enumerate(actual.rows):
        assert row.position == i
    for j, col in enumerate(actual.cols):
        assert col.position == j
    expected = [1, 2, 3, 11, 4, 5, 6, 22]
    for cell, expected_value in zip(flatten(actual.table), expected):
        assert cell.value == expected_value
