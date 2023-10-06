import asyncio
from src.spreadsheet.sheet import router


def print_hi(name):
    print(f'Hi, {name}')


async def main():
    task1 = asyncio.create_task(router.create_sheet())
    await task1


if __name__ == '__main__':
    asyncio.run(main())
    print_hi("Alex")
