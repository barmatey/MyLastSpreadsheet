from uuid import uuid4, UUID

import pytest
from pydantic import BaseModel

from src.base import broker

import db


class PubOne(BaseModel):
    id: UUID


class PubTwo(BaseModel):
    id: UUID


class SubOne(BaseModel):
    id: UUID


def pub_one_getter(uuid: UUID):
    return PubOne(id=uuid)


def pub_two_getter(uuid: UUID):
    return PubTwo(id=uuid)


def sub_one_getter(uuid: UUID):
    return SubOne(id=uuid)


@pytest.mark.asyncio
async def test_temp():
    async with db.get_async_session() as session:
        pub1 = PubOne(id=uuid4())
        pub2 = PubTwo(id=uuid4())
        sub1 = SubOne(id=uuid4())

        broker_repo = broker.BrokerRepoPostgres(session)
        broker_service = broker.BrokerPostgres(broker_repo)

        broker_service.register(PubOne, pub_one_getter)
        broker_service.register(PubTwo, pub_two_getter)
        broker_service.register(SubOne, sub_one_getter)

        await broker_service.subscribe([pub1, pub2], sub1)

        await session.commit()
