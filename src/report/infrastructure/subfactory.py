from pydantic import BaseModel

from ..subscriber import SubscriberFactory, SourceSubscriber, GroupSubscriber
from .. import domain, services, events
from ...base import eventbus
from ...base.broker import BrokerService


class ReportSubfac(SubscriberFactory):
    def __init__(self, report_service: services.ReportService, broker: BrokerService,
                 sheet_gateway: services.SheetGateway,
                 queue: eventbus.Queue):
        self._broker = broker
        self._queue = queue
        self._report_service = report_service
        self._sheet_gw = sheet_gateway

    def create_group_subscriber(self, entity: BaseModel) -> GroupSubscriber:
        if isinstance(entity, domain.Report):
            return services.ReportPublisher(entity, self._sheet_gw, self._broker)
        raise TypeError(f"{type(entity)}")

    def create_source_subscriber(self, entity: BaseModel) -> SourceSubscriber:
        if isinstance(entity, domain.Group):
            return services.GroupPublisher(entity, self._broker, self._queue)
        if isinstance(entity, domain.Report):
            return services.ReportPublisher(entity, self._sheet_gw, self._broker)
        raise TypeError
