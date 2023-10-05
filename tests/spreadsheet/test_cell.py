from src.bus.eventbus import Queue, EventBus
from src.spreadsheet.cell.domain import CellPubsub, Cell, CellCreated
from src.spreadsheet.sheet.domain import Sheet


def test_create_cell_pubsub_generate_event():
    sheet = Sheet()
    cell = Cell(sheet=sheet)
    CellPubsub(entity=cell)

    queue = Queue()
    event = queue.popleft()
    assert isinstance(event, CellCreated)


def test_created_cell_saved_in_repo():
    sheet = Sheet()
    cell = Cell(sheet=sheet)
    CellPubsub(entity=cell)
    bus = EventBus()
    bus.run()
