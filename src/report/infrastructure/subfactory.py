from pydantic import BaseModel

from ..subscriber import SubscriberFactory, SourceSubscriber
from .. import domain, services
from ...base import eventbus
from ...base.broker import BrokerService
from ...base.repo.repository import Repository


class ReportSubfac(SubscriberFactory):
    def __init__(self, broker: BrokerService, repo: Repository[domain.Report],
                 sheet_gateway: services.SheetGateway, queue: eventbus.Queue):
        self._broker = broker
        self._queue = queue
        self._sheet_gw = sheet_gateway
        self._repo = repo

    def create_source_subscriber(self, entity: BaseModel) -> SourceSubscriber:
        if isinstance(entity, domain.Report):
            return services.ReportPublisher(entity, self._repo, self._sheet_gw, self._broker)
        raise TypeError
