from src.bus.eventbus import register
from src.spreadsheet.cell.domain import CellCreated
from src.spreadsheet.cell.repository import CellRepo


class CellCreatedHandler:
    def __init__(self, repo: CellRepo):
        self._repo = repo

    @register(CellCreated)
    def handle(self, event: CellCreated) -> None:
        self._repo.add(event.entity)
