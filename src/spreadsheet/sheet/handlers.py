from src.spreadsheet.sheet import (
    events as sheet_events,
    repository as sheet_repo,
)


async def handle_sheet_created(event: sheet_events.SheetCreated, repo: sheet_repo.SheetRepo):
    await repo.add(event.entity)


async def handle_sheet_requested(event: sheet_events.SheetRequested, repo: sheet_repo.SheetRepo):
    return await repo.get_by_uuid(event.uuid)
