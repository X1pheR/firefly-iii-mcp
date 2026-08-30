from __future__ import annotations

import json
from collections.abc import Mapping
from decimal import Decimal
from enum import StrEnum
from typing import Any
from urllib.parse import quote

import httpx


class Endpoint(StrEnum):
    ABOUT = "/about"
    ACCOUNTS = "/accounts"
    ACCOUNT = "/accounts/{id}"
    TRANSACTIONS = "/transactions"
    TRANSACTION = "/transactions/{id}"
    SEARCH_TRANSACTIONS = "/search/transactions"
    BUDGETS = "/budgets"
    BUDGET_LIMITS = "/budget-limits"
    BILLS = "/bills"
    CATEGORIES = "/categories"
    TAGS = "/tags"
    PIGGY_BANKS = "/piggy-banks"
    RECURRENCES = "/recurrences"
    CURRENCIES = "/currencies"
    RULE_GROUPS = "/rule-groups"
    RULE_GROUP = "/rule-groups/{id}"
    RULES = "/rules"
    RULE = "/rules/{id}"
    EXCHANGE_RATES = "/exchange-rates/{from}/{to}"
    EXCHANGE_RATE_ON_DATE = "/exchange-rates/{from}/{to}/{date}"
    SUMMARY_BASIC = "/summary/basic"
    INSIGHT_EXPENSE_TOTAL = "/insight/expense/total"
    INSIGHT_INCOME_TOTAL = "/insight/income/total"
    INSIGHT_TRANSFER_TOTAL = "/insight/transfer/total"
    INSIGHT_EXPENSE_CATEGORY = "/insight/expense/category"


ALLOWED_ENDPOINTS = frozenset(Endpoint)


class UnsafeRequestError(RuntimeError):
    """Raised before I/O when a request would cross the read-only boundary."""


class FireflyApiError(RuntimeError):
    def __init__(self, status_code: int, endpoint: Endpoint, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.endpoint = endpoint


class FireflyUnavailable(RuntimeError):
    """Raised for timeouts and connectivity failures without leaking request details."""


def _json_loads_decimal(text: str) -> Any:
    return json.loads(text, parse_float=Decimal, parse_int=int)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    return value


class FireflyClient:
    def __init__(
        self,
        *,
        base_url: str,
        token: str,
        timeout_seconds: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            timeout=timeout_seconds,
            transport=transport,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get(
        self,
        endpoint: Endpoint,
        *,
        path_params: Mapping[str, int | str] | None = None,
        query: Mapping[str, Any] | None = None,
    ) -> Any:
        return await self._request("GET", endpoint, path_params=path_params, query=query)

    async def _request(
        self,
        method: str,
        endpoint: Endpoint,
        *,
        path_params: Mapping[str, int | str] | None = None,
        query: Mapping[str, Any] | None = None,
    ) -> Any:
        if method != "GET":
            raise UnsafeRequestError("Only HTTP GET is permitted by the Firefly III MCP client")
        if endpoint not in ALLOWED_ENDPOINTS:
            raise UnsafeRequestError("Endpoint is not in the Firefly III MCP allowlist")

        path = endpoint.value
        for key, value in (path_params or {}).items():
            placeholder = "{" + key + "}"
            if placeholder not in path:
                raise UnsafeRequestError("Unexpected path parameter")
            path = path.replace(placeholder, quote(str(value), safe=""))
        if "{" in path or "}" in path:
            raise UnsafeRequestError("Missing required path parameter")

        clean_query = {
            key: value for key, value in (query or {}).items() if value is not None and value != [] and value != ""
        }
        try:
            response = await self._client.get(path, params=clean_query)
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise FireflyUnavailable("Firefly III API is unavailable") from exc

        if not response.is_success:
            if response.status_code == 401:
                message = "Firefly III authentication failed"
            elif response.status_code == 403:
                message = "Firefly III access was denied"
            elif response.status_code == 404:
                message = "Firefly III resource was not found"
            elif response.status_code >= 500:
                message = "Firefly III server error"
            else:
                message = f"Firefly III API request failed with HTTP {response.status_code}"
            raise FireflyApiError(response.status_code, endpoint, message)

        try:
            return _json_safe(_json_loads_decimal(response.text))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise FireflyApiError(response.status_code, endpoint, "Firefly III returned malformed JSON") from exc
