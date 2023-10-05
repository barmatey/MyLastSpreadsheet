import typing
from collections import deque
from uuid import UUID, uuid4

from loguru import logger
from pydantic import BaseModel, Field

from src.bus.events import Event
from src.helpers.decorators import singleton


class Command(BaseModel):
    uuid: UUID = Field(default_factory=uuid4)


Message = Command | Event


@singleton
class Queue:
    def __init__(self):
        self._queue = deque()

    @property
    def empty(self):
        return len(self._queue) == 0

    def append(self, msg: Message):
        logger.debug(f"appended: {msg}")
        self._queue.append(msg)

    def popleft(self) -> Message:
        msg = self._queue.popleft()
        logger.debug(f"extracted: {msg}")
        return msg


@singleton
class EventBus:
    def __init__(self):
        self._events = Queue()
        self._commands = Queue()
        self._handlers: dict[typing.Type[Message], typing.Callable] = {}
        self.results: dict[UUID, typing.Any] = {}

    def _handle(self, msg: Message) -> typing.Any:
        handler = self._handlers[type(msg)]
        return handler(msg)

    def register(self, msg: typing.Type[Message]):
        def decorator(fn):
            self._handlers[msg] = fn

        return decorator

    def run(self):
        while not self._events.empty:
            event = self._events.popleft()
            self.results[event.uuid] = self._handle(event)
