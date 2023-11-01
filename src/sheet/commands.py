from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.sheet import services, domain


class GetSheetByUuid(BaseModel):
    uuid: UUID
    receiver: services.SheetService
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self) -> domain.Sheet:
        return await self.receiver.get_by_id(self.uuid)
