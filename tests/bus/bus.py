from src.bus.eventbus import Queue, EventBus
from src.bus.events import Event


def test_register_decorator():
    bus = EventBus()

    class SimpleEvent(Event):
        pass

    @bus.register(SimpleEvent)
    def simple_event_handler(_):
        return "handled"

    event = SimpleEvent()
    queue = Queue()
    queue.append(event)

    bus = EventBus()
    bus.run()

    assert bus.results[event.uuid] == "handled"
