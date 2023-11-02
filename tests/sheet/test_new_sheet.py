from datetime import datetime

from src.sheet import domain
from src.helpers.arrays import flatten


def test_drop():
    sheet: domain.Sheet = domain.Sheet.from_table([[1, 2], [3, 4], [5, 6]])
    actual = sheet.drop(sheet.rows[1].id, axis=0).drop(sheet.cols[0].id, axis=1)
    assert len(actual.rows) == 2
    assert len(actual.cols) == 1
    for i, row in enumerate(actual.rows):
        assert row.position == i
    for j, col in enumerate(actual.cols):
        assert col.position == j


def test_resize_sheet():
    sheet1 = domain.Sheet.from_table([
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
    ])
    actual = sheet1.resize(2, 2)
    assert len(actual.rows) == 2
    assert len(actual.cols) == 2
    assert len(actual.table) == 2
    assert len(actual.table[0]) == len(actual.table[1]) == 2

    actual = sheet1.resize(3, 3)
    assert len(actual.rows) == 3
    assert len(actual.cols) == 3

    actual = sheet1.resize(5, 5)
    assert len(actual.rows) == 5
    assert len(actual.cols) == 5
    assert len(actual.table) == 5
    for row in actual.table:
        assert len(row) == 5


def test_replace_cell_values():
    sheet1 = domain.Sheet.from_table([
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
    sheet1 = domain.Sheet.from_table([
        [1, 2, 3, ],
        [4, 5, 6],
    ])
    sheet2 = domain.Sheet.from_table([
        [7, 8, 9]
    ])
    sheet3 = domain.Sheet.from_table([
        [11],
        [22],
    ])

    actual = domain.concat(sheet1, sheet2, axis=0)
    assert len(actual.rows) == 3
    assert len(actual.cols) == 3
    for i, row in enumerate(actual.rows):
        assert row.position == i
    for j, col in enumerate(actual.cols):
        assert col.position == j
    for i, cell in enumerate(flatten(actual.table), start=1):
        assert cell.value == i

    actual = domain.concat(sheet1, sheet3, axis=1)
    assert len(actual.rows) == 2
    assert len(actual.cols) == 4
    for i, row in enumerate(actual.rows):
        assert row.position == i
    for j, col in enumerate(actual.cols):
        assert col.position == j
    expected = [1, 2, 3, 11, 4, 5, 6, 22]
    for cell, expected_value in zip(flatten(actual.table), expected):
        assert cell.value == expected_value


def test_complex_merge():
    print()
    sheet1 = domain.Sheet.from_table([
        [None, None, datetime(2021, 1, 1), datetime(2022, 1, 1), datetime(2023, 1, 1)],
        [1, "first", 10, 10, 10],
        [1, "second", 10, 10, 10]
    ])
    sheet2 = domain.Sheet.from_table([
        [None, None, datetime(2021, 1, 1), datetime(2023, 1, 1)],
        [1, "first", 20, 20],
        [4, "new_row", 20, 20],
        [5, "Jack", 66, 66]
    ])

    expected = [
        [None, None, datetime(2021, 1, 1), datetime(2022, 1, 1), datetime(2023, 1, 1)],
        [1.0, "first", 30, 10, 30],
        [1.0, "second", 10, 10, 10],
        [4.0, "new_row", 20, 0, 20],
        [5.0, "Jack", 66, 0, 66]
    ]
    actual = domain.complex_merge(sheet1, sheet2,
                                  left_on=[x.id for x in sheet1.cols[0:2]], right_on=[x.id for x in sheet2.cols[0:2]])
    assert str(actual) == str(expected)


def test_update_diff():
    sheet1 = domain.Sheet.from_table([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    target = (
        sheet1
        .drop(sheet1.rows[1].id, axis=0)
        .drop(sheet1.cols[0].id, axis=1)
    )
    new_rows = domain.Sheet.from_table([[77, 88]], cols=target.cols)
    target = domain.concat(target, new_rows)

    new_cols = domain.Sheet.from_table([[22], [22], [22]], rows=target.rows)
    target = domain.concat(target, new_cols, axis=1)

    target.table[0][0].value = 123_456

    diff = domain.SheetDifference.from_sheets(sheet1, target)

    assert len(diff.rows_deleted) == 1
    assert len(diff.cols_deleted) == 1
    assert len(diff.cells_deleted) == 5
    assert len(diff.rows_created) == 1
    assert len(diff.cols_created) == 1
    assert len(diff.rows_updated) == 1
    assert len(diff.cols_updated) == 2

    actual_deleted_row = diff.rows_deleted.pop()
    assert actual_deleted_row.id == sheet1.rows[1].id
    assert actual_deleted_row.position == 1

    actual_deleted_col = diff.cols_deleted.pop()
    assert actual_deleted_col.id == sheet1.cols[0].id
    assert actual_deleted_col.position == 0

    actual_appended_row = diff.rows_created.pop()
    assert actual_appended_row.id == new_rows.rows[0].id
    assert actual_appended_row.position == 2

    actual_appended_col = diff.cols_created.pop()
    assert actual_appended_col.id == new_cols.cols[0].id
    assert actual_appended_col.position == 2

    frame = sheet1.to_full_frame()
    for actual in diff.cells_deleted:
        expected = frame.loc[actual.row.id, actual.col.id]
        assert actual.value == expected.value
        assert actual.row == expected.row
        assert actual.col == expected.col

    expected = sheet1.rows[2:3]
    for actual in diff.rows_updated:
        assert actual.id in set(x.id for x in expected)

    expected = sheet1.cols[1:3]
    for actual in diff.cols_updated:
        assert actual.id in set(x.id for x in expected)

    frame = target.to_full_frame()
    for actual in diff.cells_created:
        expected = frame.loc[actual.row.id, actual.col.id]
        assert actual.value == expected.value
        assert actual.row == expected.row
        assert actual.col == expected.col

    frame = target.to_full_frame()
    for actual in diff.cells_updated:
        assert actual.value == 123_456
        assert actual.value == frame.loc[actual.row.id, actual.col.id].value
        assert sheet1.to_full_frame().loc[actual.row.id, actual.col.id].value == 2


def test_cell_contains_right_sindex_references():
    sheet1 = domain.Sheet.from_table([[1, 2, 3], [4, 5, 6]])
    for i, row in enumerate(sheet1.rows):
        for j, col in enumerate(sheet1.cols):
            assert id(row) == id(sheet1.table[i][j].row)
            assert id(col) == id(sheet1.table[i][j].col)


def test_cell_contains_right_sindex_references_after_sheet_copy():
    sheet1 = domain.Sheet.from_table([[1, 2, 3], [4, 5, 6]]).reindex(axis=0)
    for i, row in enumerate(sheet1.rows):
        for j, col in enumerate(sheet1.cols):
            assert id(row) == id(sheet1.table[i][j].row)
            assert id(col) == id(sheet1.table[i][j].col)

