from time import monotonic
from http import HTTPMethod
from asyncio import Semaphore
from collections import defaultdict
from typing import Awaitable, Callable, Unpack, Coroutine

from httpx import AsyncClient, Response

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
        logger_debug: bool = False,
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
        self.logger_debug: bool = logger_debug

    async def _get_request(self, **kwargs: Unpack[GetReqKwargs]) -> Response:
        return await self.client.get(**kwargs)

    async def _post_request(self, **kwargs: Unpack[PostReqKwargs]) -> Response:
        return await self.client.post(**kwargs)

    async def get(self, **kwargs: Unpack[GetReqKwargs]) -> Response:
        return await self.match_request(method=HTTPMethod.GET, **kwargs)

    async def post(self, **kwargs: Unpack[PostReqKwargs]) -> Response:
        return await self.match_request(method=HTTPMethod.POST, **kwargs)

    async def match_request(self, method: HTTPMethod, **kwargs: Unpack[GetReqKwargs | PostReqKwargs]) -> Response:
        match method:
            case HTTPMethod.GET:
                request_func: Callable[..., Awaitable[Response]] = self._get_request
            case HTTPMethod.POST:
                request_func: Callable[..., Awaitable[Response]] = self._post_request
            case _:
                raise ValueError(f'Invalid method: {method}')
        if self.logger_debug:
            logger.debug(f'Making {method} request, {kwargs}')
        if response := await self.do_request(request_func=request_func, kwargs=kwargs, method=method):
            return response
        logger.error(f'Failed to make {method} request')

    async def do_request(
        self,
        request_func: Callable[..., Awaitable[Response]],
        method: HTTPMethod,
        kwargs: dict
    ) -> Response:
        # await self.estimate_request_size(request=request)
        async with self.semaphore:
            for counter in range(self.retry_times):
                start_conn: float = monotonic()
                self.request_count[method] += 1
                try:
                    response: Response = await request_func(**kwargs)
                except Exception as e:
                    self.error_count[e] += 1
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

    async def estimate_request_size(self, request: Coroutine) -> None:
        req_content = getattr(request, '__self__', None)
        if req_content and hasattr(req_content, 'content'):
            self.request_size += len(req_content.content)

    async def statistics(self) -> None:
        total_time: float = monotonic() - self.start_time
        total_time_microseconds: float = total_time * 1_000_000  # Convert seconds to microseconds

        statistics: OutputStatistics = OutputStatistics(
            error_count={str(e): count for e, count in self.error_count.items()},
            request_count=dict(self.request_count),
            status_code_count=dict(self.status_code_count),
            response_time=self.response_time,
            retried_count=self.retried_count,
            request_size_bytes=self.request_size,
            request_size_mb=self.request_size / consts.MB,
            response_size=self.response_size,
            total_time=total_time,
            total_time_microseconds=total_time_microseconds,
            total_time_seconds=total_time,
            total_time_minutes=total_time / consts.MINUTE,
            total_time_hours=total_time / consts.HOUR
        )

        stats_lines = [
            '\n\n📊 <bold><green>**DataDroneClient Statistics**</green></bold> 📈',
            f'⏱️ **Total Time**: <cyan>{statistics.total_time_seconds:.2f} seconds</cyan> '
            f'(<cyan>{statistics.total_time_minutes:.2f} minutes</cyan>, '
            f'<cyan>{statistics.total_time_hours:.2f} hours</cyan>, '
            f'<cyan>{statistics.total_time_microseconds:.2f} μs</cyan>)',
            f'📬 **Total Requests**: <bold>{sum(statistics.request_count.values())}</bold>',
            '\n🔍 **Request Counts by HTTP Method:**'
        ]

        for method, count in statistics.request_count.items():
            stats_lines.append(f'  - **<blue>{method.upper()}</blue>**: <bold>{count}</bold>')

        stats_lines.extend([
            '',
            '🟢 **Status Codes:**',
            '| <bold>Status Code</bold> | <bold>Description</bold>         | <bold>Count</bold> |',
            '|------------------------|---------------------------------|-------|'
        ])
        for code, count in sorted(statistics.status_code_count.items()):
            if 200 <= code < 300:
                status = '<green>✅ Success</green>'
            elif 400 <= code < 500:
                status = '<yellow>⚠️ Client Error</yellow>'
            elif 500 <= code < 600:
                status = '<red>❌ Server Error</red>'
            else:
                status = '<blue>🔵 Other</blue>'
            stats_lines.append(f'| {code} | {status} | <bold>{count}</bold> |')

        if statistics.error_count:
            stats_lines.extend([
                '',
                '🐛 **Errors:**',
                '| <bold>Error Type</bold>           | <bold>Count</bold> |',
                '|----------------------------------|-------|'
            ])
            for error, count in statistics.error_count.items():
                stats_lines.append(f'| <magenta>{error}</magenta> | <bold>{count}</bold> |')
        else:
            stats_lines.append('\n🎉 **Errors:** <green>None</green>')

        stats_lines.extend([
            '',
            f'🔄 **Total Retries**: <bold>{statistics.retried_count}</bold>',
        ])

        stats_lines.extend([
            '',
            '📦 **Data Sizes:**',
            '| <bold>Data Type</bold>   | <bold>Size (Bytes)</bold> | <bold>Size (MB)</bold> |',
            '|-----------------------|--------------------------|-----------|',
            f'| **Request**           | <bold>{statistics.request_size_bytes}</bold> | '
            f'<bold>{statistics.request_size_mb:.2f}</bold> |',
            f'| **Response**          | <bold>{statistics.response_size}</bold> | - |',
        ])

        if statistics.response_time:
            avg_response_time = sum(statistics.response_time) / len(statistics.response_time)
            max_response_time = max(statistics.response_time)
            min_response_time = min(statistics.response_time)
            stats_lines.extend([
                '',
                '⏰ **Response Time Statistics:**',
                '| <bold>Metric</bold> | <bold>Time (Seconds)</bold> |',
                '|--------------------|---------------------------|',
                f'| **Average**        | <bold>{avg_response_time:.2f}</bold> |',
                f'| **Max**            | <bold>{max_response_time:.2f}</bold> |',
                f'| **Min**            | <bold>{min_response_time:.2f}</bold> |',
            ])
        else:
            stats_lines.append('\n⏰ **Response Time:** <yellow>No responses recorded</yellow>')

        stats_str = '\n'.join(stats_lines)

        logger.info(stats_str)
