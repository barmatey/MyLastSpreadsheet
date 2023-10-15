import pytest

from src.spreadsheet import domain, services


@pytest.mark.asyncio
async def test_expand_formulas():
    size = (5, 3)
    sf = domain.SheetInfo(size=size)
    rows = [domain.RowSindex(position=i, sf=sf) for i in range(0, size[0])]
    cols = [domain.ColSindex(position=j, sf=sf) for j in range(0, size[1])]
    from_cells = [domain.Cell(sf=sf, row=rows[0], col=cols[j], value=j) for j in range(0, size[1])]

    to_cells = []
    for i in range(1, size[0]):
        for j in range(0, size[1]):
            to_cells.append(domain.Cell(sf=sf, row=rows[i], col=cols[j], value=None))

    await services.expand_formulas(from_cells, to_cells)

    temp = from_cells + to_cells
    print()
    for i in range(0, size[0]):
        print()
        for j in range(0, size[1]):
            print(temp[i * size[1] + j].value, end="\t")
