from ssl import SSLContext
from typing import Any, Callable, Mapping, TypedDict

from httpx import URL, Limits, AsyncBaseTransport
from httpx._client import EventHook, UseClientDefault
from httpx._types import (
    AuthTypes, CertTypes, CookieTypes, HeaderTypes, ProxyTypes, QueryParamTypes, RequestContent, RequestData,
    RequestExtensions, RequestFiles, TimeoutTypes
)
from pydantic import BaseModel


# arbitrary_types_allowed
class OutputStatistics(BaseModel):
    error_count: dict[str, int] | None = None
    request_count: dict[str, int] | None = None
    status_code_count: dict[int, int] | None = None
    response_time: list[float] | None = None
    retried_count: int
    request_size_bytes: int
    request_size_mb: float
    response_size: int
    total_time: float
    total_time_microseconds: float
    total_time_seconds: float
    total_time_minutes: float
    total_time_hours: float


class AsyncClientKwargs(TypedDict, total=False):
    auth: AuthTypes | None
    params: QueryParamTypes | None
    headers: HeaderTypes | None
    cookies: CookieTypes | None
    verify: SSLContext | str | bool
    cert: CertTypes | None
    http1: bool
    http2: bool
    proxy: ProxyTypes | None
    mounts: (Mapping[str, AsyncBaseTransport | None]) | None
    timeout: TimeoutTypes
    follow_redirects: bool
    limits: Limits
    max_redirects: int
    event_hooks: Mapping[str, list[EventHook]] | None
    base_url: URL | str
    transport: AsyncBaseTransport | None
    trust_env: bool
    default_encoding: str | Callable[[bytes], str]


class GetReqKwargs(TypedDict, total=False):
    url: URL | str
    params: QueryParamTypes | None
    headers: HeaderTypes | None
    cookies: CookieTypes | None
    auth: AuthTypes | UseClientDefault | None
    follow_redirects: bool | UseClientDefault
    timeout: TimeoutTypes | UseClientDefault
    extensions: RequestExtensions | None


class PostReqKwargs(TypedDict, total=False):
    url: URL | str
    content: RequestContent | None
    data: RequestData | None
    files: RequestFiles | None
    json: Any | None
    params: QueryParamTypes | None
    headers: HeaderTypes | None
    cookies: CookieTypes | None
    auth: AuthTypes | UseClientDefault
    follow_redirects: bool | UseClientDefault
    timeout: TimeoutTypes | UseClientDefault
    extensions: RequestExtensions | None
