from __future__ import annotations

import logging

import httpx
import pytest

from firefly_iii_mcp.client import Endpoint, FireflyApiError, FireflyClient, FireflyUnavailable, UnsafeRequestError


@pytest.mark.asyncio
async def test_bearer_header_is_sent_without_logging_token(caplog: pytest.LogCaptureFixture) -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, text='{"data":{"id":"0","attributes":{}}}')

    token = "super-secret-financial-token"
    client = FireflyClient(base_url="http://firefly.test/api/v1", token=token, transport=httpx.MockTransport(handler))
    caplog.set_level(logging.DEBUG)
    await client.get(Endpoint.ABOUT)
    await client.aclose()
    assert seen[0].headers["Authorization"] == f"Bearer {token}"
    assert token not in caplog.text


@pytest.mark.asyncio
async def test_authentication_failure_is_sanitized() -> None:
    client = FireflyClient(
        base_url="http://firefly.test/api/v1",
        token="secret",
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(401, text='{"message":"token secret should not escape"}')
        ),
    )
    with pytest.raises(FireflyApiError, match="authentication failed") as exc_info:
        await client.get(Endpoint.ACCOUNTS)
    assert "token secret should not escape" not in str(exc_info.value)
    await client.aclose()


@pytest.mark.parametrize("status", [400, 403, 404, 422, 500, 503])
@pytest.mark.asyncio
async def test_http_errors_are_sanitized(status: int) -> None:
    client = FireflyClient(
        base_url="http://firefly.test/api/v1",
        token="secret",
        transport=httpx.MockTransport(lambda _request: httpx.Response(status, text='{"sensitive":"details"}')),
    )
    with pytest.raises(FireflyApiError) as exc_info:
        await client.get(Endpoint.ACCOUNTS)
    assert exc_info.value.status_code == status
    assert "sensitive" not in str(exc_info.value)
    await client.aclose()


@pytest.mark.asyncio
async def test_timeout_is_mapped_without_request_details() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("sensitive query", request=request)

    client = FireflyClient(
        base_url="http://firefly.test/api/v1", token="secret", transport=httpx.MockTransport(handler)
    )
    with pytest.raises(FireflyUnavailable, match="unavailable") as exc_info:
        await client.get(Endpoint.SEARCH_TRANSACTIONS, query={"query": "private search"})
    assert "private search" not in str(exc_info.value)
    await client.aclose()


@pytest.mark.asyncio
async def test_malformed_json_is_rejected() -> None:
    client = FireflyClient(
        base_url="http://firefly.test/api/v1",
        token="secret",
        transport=httpx.MockTransport(lambda _request: httpx.Response(200, text="not-json")),
    )
    with pytest.raises(FireflyApiError, match="malformed JSON"):
        await client.get(Endpoint.ABOUT)
    await client.aclose()


@pytest.mark.asyncio
async def test_non_get_method_is_rejected_before_network_io() -> None:
    requests = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        return httpx.Response(200, text="{}")

    client = FireflyClient(
        base_url="http://firefly.test/api/v1", token="secret", transport=httpx.MockTransport(handler)
    )
    with pytest.raises(UnsafeRequestError, match="Only HTTP GET"):
        await client._request("POST", Endpoint.TRANSACTIONS)
    assert requests == 0
    await client.aclose()


@pytest.mark.asyncio
async def test_unexpected_path_parameter_is_rejected_before_network_io() -> None:
    client = FireflyClient(
        base_url="http://firefly.test/api/v1",
        token="secret",
        transport=httpx.MockTransport(lambda _request: httpx.Response(200)),
    )
    with pytest.raises(UnsafeRequestError, match="Unexpected path parameter"):
        await client.get(Endpoint.ACCOUNT, path_params={"evil": "transactions"})
    await client.aclose()


@pytest.mark.asyncio
async def test_decimal_json_numbers_become_strings() -> None:
    client = FireflyClient(
        base_url="http://firefly.test/api/v1",
        token="secret",
        transport=httpx.MockTransport(lambda _request: httpx.Response(200, text='{"value":12.34567890123456789}')),
    )
    result = await client.get(Endpoint.SUMMARY_BASIC)
    assert result == {"value": "12.34567890123456789"}
    assert not isinstance(result["value"], float)
    await client.aclose()
