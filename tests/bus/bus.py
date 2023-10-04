from src.bus.eventbus import Event, Queue, EventBus, register


def test_register_decorator():
    class SimpleEvent(Event):
        pass

    @register(SimpleEvent)
    def simple_event_handler(_):
        return "handled"

    event = SimpleEvent()
    queue = Queue()
    queue.append(event)

    bus = EventBus()
    bus.run()

    assert bus.results[event.uuid] == "handled"
