from src.sheet.domain import *
from datetime import datetime


def test_sum_two_sheets():
    sheet1 = Sheet.from_table([[1, 1], [1, 1]])
    actual = sheet1 + sheet1

    expected = f"{[[2, 2], [2, 2]]}"
    actual = f"{actual.to_table()}"
    assert actual == expected

    expected = f"{[[1, 1], [1, 1]]}"
    actual = f"{sheet1.to_table()}"
    assert actual == expected





def test_update_diff():
    sheet1 = Sheet.from_table([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    target = (
        sheet1
        .drop(sheet1.rows[1].id, axis=0)
        .drop(sheet1.cols[0].id, axis=1)
    )
    new_rows = Sheet.from_table([[77, 88]], cols=target.cols)
    target = target.concat(new_rows)

    new_cols = Sheet.from_table([[22], [22], [22]], rows=target.rows)
    target = target.concat(new_cols, axis=1)

    target.frame.iloc[0, 0].value = 123_456

    diff = SheetDifference(sheet1, target)
    diff.find_updates()

    assert len(diff.deleted_rows) == 1
    assert len(diff.deleted_cols) == 1
    assert len(diff.deleted_cells) == 5
    assert len(diff.appended_rows) == 1
    assert len(diff.appended_cols) == 1
    assert len(diff.moved_rows) == 1
    assert len(diff.moved_cols) == 2

    actual_deleted_row = diff.deleted_rows.pop()
    assert actual_deleted_row.id == sheet1.rows[1].id
    assert actual_deleted_row.position == 1

    actual_deleted_col = diff.deleted_cols.pop()
    assert actual_deleted_col.id == sheet1.cols[0].id
    assert actual_deleted_col.position == 0

    actual_appended_row = diff.appended_rows.pop()
    assert actual_appended_row.id == new_rows.rows[0].id
    assert actual_appended_row.position == 2

    actual_appended_col = diff.appended_cols.pop()
    assert actual_appended_col.id == new_cols.cols[0].id
    assert actual_appended_col.position == 2

    for actual in diff.deleted_cells:
        expected = sheet1.frame.loc[actual.row_id, actual.col_id]
        assert actual.value == expected.value
        assert actual.row_id == expected.row_id
        assert actual.col_id == expected.col_id

    expected = sheet1.rows[2:3]
    for actual in diff.moved_rows:
        assert actual.id in set(x.id for x in expected)

    expected = sheet1.cols[1:3]
    for actual in diff.moved_cols:
        assert actual.id in set(x.id for x in expected)

    for actual in diff.appended_cells:
        expected = target.frame.loc[actual.row_id, actual.col_id]
        assert actual.value == expected.value
        assert actual.row_id == expected.row_id
        assert actual.col_id == expected.col_id

    for actual in diff.updated_cells:
        assert actual.value == 123_456
        assert actual.value == target.frame.loc[actual.row_id, actual.col_id].value
        assert sheet1.frame.loc[actual.row_id, actual.col_id].value == 2







def test_complex_merge():
    sheet1 = Sheet.from_table([
        [None, None, datetime(2021, 1, 1), datetime(2022, 1, 1), datetime(2023, 1, 1)],
        [1, "first", 10, 10, 10],
        [1, "second", 10, 10, 10]
    ])
    sheet2 = Sheet.from_table([
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
    actual = (
        ComplexMerge(sheet1, sheet2)
        .merge(list(sheet1.frame.columns[0:2]), list(sheet2.frame.columns[0:2]))
        .to_table()
    )
    assert str(actual) == str(expected)
