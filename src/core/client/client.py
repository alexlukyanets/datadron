from typing import Any
from time import monotonic
from http import HTTPMethod
from asyncio import Semaphore
from collections import defaultdict

from httpx import AsyncClient, Response

from logger import logger

from core.client import consts
from core.client.models import OutputStatistics


class DataDroneClient:
    def __init__(
        self,
        *,
        async_tasks: int = consts.ASYNC_TASKS,
        retry_times: int = consts.RETRY_TIMES,
        headers: dict[str, str] = None
    ) -> None:
        self.start_time: float = monotonic()
        self.semaphore: Semaphore = Semaphore(value=async_tasks)
        self.retry_times: int = retry_times
        self.headers: dict[str, str] = headers or {}
        self.error_count: dict[Exception, int] = defaultdict(int)
        self.request_count: dict[str, int] = defaultdict(int)
        self.status_code_count: dict[int, int] = defaultdict(int)
        self.retried_count: int = 0
        self.request_size: int = 0
        self.response_size: int = 0
        self.response_time: list[float] = []
        self.client: AsyncClient = AsyncClient(headers=self.headers)

    async def get(self, url: str, params: dict[str, Any]) -> Response:
        return await self._send_request(HTTPMethod.GET, url, params=params)

    async def post(self, url: str, data: dict[str, Any]) -> Response:
        return await self._send_request(HTTPMethod.POST, url, json=data)

    async def _send_request(self, method: str, url: str, **kwargs) -> Response:
        async with self.semaphore:
            for _ in range(self.retry_times):
                try:
                    response = await self.client.request(method, url, **kwargs)
                    self._log_request(method, response)
                    if response.is_success:
                        return response
                    self.retried_count += 1
                except Exception as e:
                    self._handle_exception(e)
                continue
            raise ConnectionError(f"Failed to perform {method} request after retries.")

    def _log_request(self, method: str, response: Response) -> None:
        self.request_count[method] += 1
        self.status_code_count[response.status_code] += 1
        self.response_time.append(monotonic() - self.start_time)

    def _handle_exception(self, exception: Exception) -> None:
        logger.error(f'Error during request: {exception!r}')
        self.error_count[exception] += 1

    async def statistics(self) -> OutputStatistics:
        total_time: float = monotonic() - self.start_time
        return OutputStatistics(
            error_count=self.error_count,
            request_count=self.request_count,
            status_code_count=self.status_code_count,
            response_time=self.response_time,
            retried_count=self.retried_count,
            request_size_bytes=self.request_size,
            request_size_mb=self.request_size / consts.MB,
            response_size=self.response_size,
            total_time_seconds=total_time,
            total_time_minutes=total_time / consts.MINUTE,
            total_time_hours=total_time / consts.HOUR,
            total_time=total_time
        )
