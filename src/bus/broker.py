from src.helpers.decorators import singleton


@singleton
class Broker:
    def __init__(self):
        self._subscribers = {}

    def subscribe(self, pub, sub):
        if self._subscribers.get(pub) is None:
            self._subscribers[pub] = set()
        self._subscribers[pub].add(sub)

    def subscribe_to_many(self, pubs, sub):
        for pub in pubs:
            self.subscribe(pub, sub)

    def unsubscribe(self, pub, sub):
        self._subscribers[pub].remove(sub)
        if len(self._subscribers[pub]) == 0:
            del self._subscribers[pub]

    def unsubscribe_from_many(self, pubs, sub):
        for pub in pubs:
            self.unsubscribe(pub, sub)

    def get_subscribers(self, pub):
        return self._subscribers[pub]
