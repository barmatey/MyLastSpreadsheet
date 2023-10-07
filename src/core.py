from collections import namedtuple
from typing import Union, NamedTuple

from pydantic import BaseModel, ConfigDict


class OrderBy(NamedTuple):
    fields: Union[str, list[str]]
    asc: bool


class PydanticModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
