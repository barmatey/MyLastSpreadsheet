from src.bus.eventbus import Event, Queue, EventBus, register


class SimpleEvent(Event):
    pass


@register(SimpleEvent)
def simple_event_handler(ev):
    return "handled1"


def test_temp():
    event = SimpleEvent()
    queue = Queue()
    queue.append(event)

    bus = EventBus()
    bus.run()

    assert bus.results[event.uuid] == "handled"
