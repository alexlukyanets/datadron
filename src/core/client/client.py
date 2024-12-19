from asyncio import Semaphore
from collections import defaultdict

from httpx import AsyncClient

from core.client import consts


class DataDroneClient:
    client: AsyncClient = AsyncClient()

    def __init__(
        self,
        async_tasks: int = consts.ASYNC_TASKS,
        retry_times: int = consts.RETRY_TIMES,
        headers: dict[str, str] | None = None
    ):
        self.semaphore: Semaphore = Semaphore(value=async_tasks)
        self.retry_times: int = retry_times
        self.status_counter: dict[int, int] = defaultdict(int)
        self.headers: dict[str, str] | None = headers
        self.random_user_agent: bool = False

    async def request(self, method: str, url: str, **kwargs):
        return await self.client.request(method, url, **kwargs)
