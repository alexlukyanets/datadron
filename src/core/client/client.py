from asyncio import Semaphore
from http import HTTPMethod
from typing import Unpack, Coroutine

from httpx import AsyncClient, Response

from logger import logger

from core.client import consts
from core.client.models import AsyncClientKwargs, GetRequestKwargs, PostRequestKwargs


class DataDroneClient:

    def __init__(
        self,
        async_tasks: int = consts.ASYNC_TASKS,
        retry_times: int = consts.RETRY_TIMES,
        headers: dict[str, str] | None = None,
        **kwargs: Unpack[AsyncClientKwargs],
    ):
        self.client: AsyncClient = AsyncClient(**kwargs)
        self.semaphore: Semaphore = Semaphore(value=async_tasks)
        self.retry_times: int = retry_times
        self.headers: dict[str, str] | None = headers
        self.random_user_agent: bool = False

    async def get(self, **kwargs: Unpack[GetRequestKwargs]) -> Response:
        return await self.match_request(method=HTTPMethod.GET, **kwargs)

    async def post(self, **kwargs: Unpack[PostRequestKwargs]) -> Response:
        return await self.match_request(method=HTTPMethod.POST, **kwargs)

    async def match_request(self, method: str, **kwargs: Unpack[GetRequestKwargs | PostRequestKwargs]) -> Response:
        match method:
            case HTTPMethod.GET:
                request: Coroutine = self.get(**kwargs)
            case HTTPMethod.POST:
                request: Coroutine = self.post(**kwargs)
            case _:
                raise ValueError(f'Invalid method: {method}')
        if response := await request:
            return response
        logger.error(f'Failed to make {method} request')

    async def do_request(self, request: Coroutine) -> Response:
        async with self.semaphore:
            for counter in range(self.retry_times):
                try:
                    response: Response = await request
                except Exception as e:
                    continue
                if not response.is_success:
                    continue
                return response

    async def statistics(self):
        # status code counter
        # retry times counter
        # request times counter
        # request time counter
        # request size counter
        # response size counter
        # connection time counter
        # response time counter
        return
