import pytest

from src.base.cell import Cell, CellService, CellSubscriber, CellSelfSubscriber
from src.base.service import RepoPostgres, Service, Queue, Repository, Broker


@pytest.mark.asyncio
async def test_start():
    queue = Queue()
    broker = Broker()
    cell1 = Cell(value=11)
    cell2 = Cell(value=44)
    repo: Repository[Cell] = RepoPostgres()
    cell_service: Service[Cell] = CellService(repo=repo, queue=queue)
    cell_sub: CellSubscriber = CellSelfSubscriber(cell2, cell_service, broker)
    await cell_sub.follow_cells([cell1])

    print(f"\n\n{cell2}\n", cell_sub.entity)
