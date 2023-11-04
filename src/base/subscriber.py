from abc import ABC
from typing import Any


class Subscriber(ABC):
    @property
    def entity(self):
        raise NotImplemented

    @property
    def secondary_data(self) -> dict[str, Any]:
        raise NotImplemented
