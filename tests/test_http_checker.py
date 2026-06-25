import httpx

from app.services.http_checker import HttpChecker


async def test_http_checker_successful_check() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200)

    result = await HttpChecker(httpx.MockTransport(handler)).check("https://example.com/health", 5)

    assert result.http_status == 200
    assert result.latency_ms is not None
    assert result.error_type is None


async def test_http_checker_unexpected_status_code() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    result = await HttpChecker(httpx.MockTransport(handler)).check("https://example.com/health", 5)

    assert result.http_status == 500
    assert result.error_type is None


async def test_http_checker_timeout() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("too slow", request=request)

    result = await HttpChecker(httpx.MockTransport(handler)).check("https://example.com/health", 5)

    assert result.http_status is None
    assert result.error_type == "timeout"
    assert result.error_message == "too slow"


async def test_http_checker_connection_error() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("dns failed", request=request)

    result = await HttpChecker(httpx.MockTransport(handler)).check("https://example.com/health", 5)

    assert result.http_status is None
    assert result.error_type == "ConnectError"
    assert result.error_message == "dns failed"
