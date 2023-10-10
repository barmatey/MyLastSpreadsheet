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


class Queue:
    def __init__(self):
        self._queue = deque()
        logger.debug(f"CONSTRUCTOR =========================================")

    @property
    def empty(self):
        return len(self._queue) == 0

    def append(self, msg: Message):
        logger.debug(f"appended: {msg} {id(self)}")
        self._queue.append(msg)

    def popleft(self) -> Message:
        msg = self._queue.popleft()
        logger.debug(f"extracted: {msg} {id(self)}")
        return msg


class EventBus:
    def __init__(self, queue: Queue):
        self._events = queue
        self._handlers: dict[typing.Type[Message], typing.Callable] = {}
        self._handler_kwargs: dict[typing.Type[Message], dict] = {}
        self.results: dict[UUID, typing.Any] = {}

    async def _handle(self, msg: Message) -> typing.Any:
        key = type(msg)
        handler = self._handlers[key]
        kwargs = self._handler_kwargs[key]
        return await handler(msg, **kwargs)

    def register(self, msg: typing.Type[Message]):
        def decorator(fn):
            self._handlers[msg] = fn
        return decorator

    def add_handler(self, event: typing.Type[Event], fn: typing.Callable, kwargs: dict = None):
        self._handlers[event] = fn
        if kwargs is None:
            kwargs = {}
        self._handler_kwargs[event] = kwargs

    async def run(self):
        while not self._events.empty:
            event = self._events.popleft()
            self.results[event.uuid] = await self._handle(event)
