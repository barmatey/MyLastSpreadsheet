from collections import namedtuple
from typing import Union, NamedTuple, TypeVar, Sequence

from pydantic import BaseModel, ConfigDict


class OrderBy(NamedTuple):
    fields: Union[str, list[str]]
    asc: bool


class PydanticModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


T = TypeVar("T")
Table = list[list[T]]
