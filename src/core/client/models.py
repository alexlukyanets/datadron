from ssl import SSLContext
from typing import Any, Callable, Mapping, TypedDict

from httpx import URL, Limits, AsyncBaseTransport
from httpx._client import EventHook, UseClientDefault
from httpx._types import (
    AuthTypes, CertTypes, CookieTypes, HeaderTypes, ProxyTypes, QueryParamTypes, RequestContent, RequestData,
    RequestExtensions, RequestFiles, TimeoutTypes
)


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


class GetRequestKwargs(TypedDict, total=False):
    url: URL | str
    params: QueryParamTypes | None
    headers: HeaderTypes | None
    cookies: CookieTypes | None
    auth: AuthTypes | UseClientDefault | None
    follow_redirects: bool | UseClientDefault
    timeout: TimeoutTypes | UseClientDefault
    extensions: RequestExtensions | None


class PostRequestKwargs(TypedDict, total=False):
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
