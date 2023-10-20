from pydantic import BaseModel

from ..subscriber import SubscriberFactory, SourceSubscriber
from .. import domain, services
from ...base import eventbus
from ...base.broker import BrokerService


class ReportSubfac(SubscriberFactory):
    def __init__(self, broker: BrokerService, sheet_gateway: services.SheetGateway, queue: eventbus.Queue):
        self._broker = broker
        self._queue = queue
        self._sheet_gw = sheet_gateway

    def create_source_subscriber(self, entity: BaseModel) -> SourceSubscriber:
        if isinstance(entity, domain.Report):
            return services.ReportPublisher(entity, self._sheet_gw, self._broker)
        raise TypeError
