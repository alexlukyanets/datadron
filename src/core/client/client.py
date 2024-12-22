from time import monotonic
from http import HTTPMethod
from asyncio import Semaphore
from collections import defaultdict
from typing import Unpack, Coroutine

from httpx import (
    AsyncClient, ConnectTimeout, CookieConflict, DecodingError, HTTPStatusError, NetworkError, PoolTimeout,
    ProtocolError, ReadTimeout, RemoteProtocolError, Response, WriteTimeout
)

from logger import logger

from core.client import consts
from core.client.models import AsyncClientKwargs, GetReqKwargs, OutputStatistics, PostReqKwargs


class DataDroneClient:
    def __init__(
        self,
        *,
        async_tasks: int = consts.ASYNC_TASKS,
        retry_times: int = consts.RETRY_TIMES,
        headers: dict[str, str] | None = None,
        **kwargs: Unpack[AsyncClientKwargs],
    ):
        self.start_time: float = monotonic()
        self.client: AsyncClient = AsyncClient(**kwargs)
        self.semaphore: Semaphore = Semaphore(value=async_tasks)
        self.retry_times: int = retry_times
        self.headers: dict[str, str] | None = headers
        self.random_user_agent: bool = False
        self.error_count: dict[Exception, int] = defaultdict(int)
        self.request_count: dict[HTTPMethod, int] = defaultdict(int)
        self.status_code_count: dict[int, int] = defaultdict(int)
        self.retried_count: int = 0
        self.request_size: int = 0
        self.response_size: int = 0
        self.response_time: list[float] = []

    async def get(self, **kwargs: Unpack[GetReqKwargs]) -> Response:
        return await self.match_request(method=HTTPMethod.GET, **kwargs)

    async def post(self, **kwargs: Unpack[PostReqKwargs]) -> Response:
        return await self.match_request(method=HTTPMethod.POST, **kwargs)

    async def match_request(self, method: HTTPMethod, **kwargs: Unpack[GetReqKwargs | PostReqKwargs]) -> Response:
        match method:
            case HTTPMethod.GET:
                request: Coroutine = self.get(**kwargs)
            case HTTPMethod.POST:
                request: Coroutine = self.post(**kwargs)
            case _:
                raise ValueError(f'Invalid method: {method}')
        self.request_count[method] += 1
        if response := await self.do_request(request=request):
            return response
        logger.error(f'Failed to make {method} request')

    async def do_request(self, request: Coroutine) -> Response:
        await self.estimate_request_size(request=request)
        async with self.semaphore:
            for counter in range(self.retry_times):
                start_conn: float = monotonic()
                try:
                    response: Response = await self.handle_error_request(request=request)
                except Exception as e:
                    logger.error(f'Failed to make request: {e!r}')
                    self.retried_count += 1
                    continue
                self.response_time.append(monotonic() - start_conn)
                self.status_code_count[response.status_code] += 1
                if not response.is_success:
                    self.retried_count += 1
                    continue
                if response.content:
                    self.response_size += len(response.content)
                return response

    async def handle_error_request(self, request: Coroutine, e: None = None) -> Response:
        try:
            return await self.do_request(request)
        except ConnectTimeout as e:
            logger.error(f'Connection timeout')
        except ReadTimeout as e:
            logger.error(f'Read timeout')
        except WriteTimeout as e:
            logger.error(f'Write timeout')
        except PoolTimeout as e:
            logger.error(f'Pool timeout')
        except NetworkError as e:
            logger.error(f'Network error')
        except HTTPStatusError as e:
            logger.error(f'HTTP status error')
        except DecodingError as e:
            logger.error(f'Decoding error')
        except RemoteProtocolError as e:
            logger.error(f'Remote protocol error')
        except ProtocolError as e:
            logger.error(f'Protocol error')
        except CookieConflict as e:
            logger.error(f'Cookie conflict')
        finally:
            self.error_count[e] += 1

    async def estimate_request_size(self, request: Coroutine) -> None:
        req_content = getattr(request, '__self__', None)
        if req_content and hasattr(req_content, 'content'):
            self.request_size += len(req_content.content)

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
            total_time=total_time,
            total_time_seconds=total_time,
            total_time_minutes=total_time / consts.MINUTE,
            total_time_hours=total_time / consts.HOUR
        )
