import asyncio
from src.spreadsheet.sheet_meta import router


def print_hi(name):
    print(f'Hi, {name}')


async def main():
    task1 = asyncio.create_task(router.create_sheet())
    sheet_id = await task1

    task2 = asyncio.create_task(router.get_sheet(sheet_id))
    sheet = await task2

    table = [[1, 2], [3, 4], [5, 6]]
    task3 = asyncio.create_task(router.append_rows(sheet, table))
    await task3

    task4 = asyncio.create_task(router.get_sheet(sheet_id))
    sheet = await task4

    print(sheet)


if __name__ == '__main__':
    asyncio.run(main())
    print_hi("Alex")
