from abc import ABC


class Subscriber(ABC):
    @property
    def entity(self):
        raise NotImplemented
