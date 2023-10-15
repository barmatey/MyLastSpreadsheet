from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field


class Wire(BaseModel):
    date: datetime
    sender: float
    receiver: float
    amount: float
    sub1: str = ""
    sub2: str = ""
    id: UUID = Field(default_factory=uuid4)
