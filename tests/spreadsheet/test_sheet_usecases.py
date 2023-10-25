import pytest

from src.spreadsheet.domain import Sheet
from src.spreadsheet import services


@pytest.mark.asyncio
async def test_temp():
    print("\n\n")
    sheet1 = Sheet.from_table([
        ["first", 11],
        ["second", 22],
    ])
    sheet2 = Sheet.from_table([
        ["first", 77],
        ["new_row", 1000],
        ["JackDaniels", 123]
    ])
    uc = services.SumOrAppendRows().load_data(sheet1, sheet2, on=[0])
    uc.validate()
    await uc.execute()
