from src.sheet import schema, usecases


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




def test_update_diff():
    sheet1 = schema.Sheet.from_table([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    target = (
        sheet1
        .drop(sheet1.rows[1].id, axis=0)
        .drop(sheet1.cols[0].id, axis=1)
    )
    new_rows = schema.Sheet.from_table([[77, 88]], cols=target.cols)
    target = target.concat(new_rows)

    new_cols = schema.Sheet.from_table([[22], [22], [22]], rows=target.rows)
    target = target.concat(new_cols, axis=1)

    target.frame.iloc[0, 0].value = 123_456

    diff = usecases.SheetDifference(sheet1, target)
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
