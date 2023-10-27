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


async def pub_one_getter(uuids: list[UUID]):
    result = [PubOne(id=x) for x in uuids]
    return result


async def pub_two_getter(uuids: list[UUID]):
    result = [PubTwo(id=x) for x in uuids]
    return result


async def sub_one_getter(uuids: list[UUID]):
    result = [SubOne(id=x) for x in uuids]
    return result


@pytest.mark.asyncio
async def test_temp():
    async with db.get_async_session() as session:
        pub1 = PubOne(id=uuid4())
        pub2 = PubTwo(id=uuid4())
        sub1 = SubOne(id=uuid4())
        sub2 = SubOne(id=uuid4())

        broker_repo = broker.BrokerRepoPostgres(session)
        broker_service = broker.BrokerPostgres(broker_repo)

        broker_service.register(PubOne, pub_one_getter)
        broker_service.register(PubTwo, pub_two_getter)
        broker_service.register(SubOne, sub_one_getter)

        await broker_service.subscribe([pub1, pub2], sub1)
        await broker_service.subscribe([pub1, pub2], sub2)

        subs = await broker_service.get_subs(pub1)
        print(subs)

        await session.commit()
