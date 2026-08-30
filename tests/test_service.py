from __future__ import annotations

from datetime import date

import httpx
import pytest

from firefly_iii_mcp.client import FireflyClient
from firefly_iii_mcp.service import FireflyService, InputError


@pytest.mark.asyncio
async def test_transaction_list_is_bounded_and_minimized(
    service: FireflyService, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FixedDate(date):
        @classmethod
        def today(cls) -> FixedDate:
            return cls(2026, 8, 30)

    monkeypatch.setattr("firefly_iii_mcp.service.date", FixedDate)
    result = await service.list_transactions()
    assert result["coverage"] == {"start": "2026-08-01", "end": "2026-08-30"}
    split = result["transactions"][0]["transactions"][0]
    assert split["amount"] == "12.34"
    assert "notes" not in split
    assert "internal_reference" not in split
    assert result["pagination"]["returned"] == 1


@pytest.mark.asyncio
async def test_notes_require_explicit_opt_in(service: FireflyService) -> None:
    result = await service.get_transaction(10, include_notes=True)
    assert result["transactions"][0]["notes"] == "private note"


@pytest.mark.asyncio
async def test_account_notes_require_explicit_opt_in(service: FireflyService) -> None:
    minimized = await service.get_account(1)
    detailed = await service.get_account(1, include_notes=True)
    assert "notes" not in minimized
    assert detailed["notes"] == "private account note"


@pytest.mark.asyncio
async def test_budget_status_uses_decimal_arithmetic(service: FireflyService) -> None:
    result = await service.get_budget_status("2026-08-01", "2026-08-31")
    limit = result["budgets"][0]["limits"][0]
    assert limit["amount"] == "500.00"
    assert limit["spent"] == "-125.25"
    assert limit["remaining"] == "374.75"


@pytest.mark.asyncio
async def test_monthly_summary_has_exact_month_coverage_and_no_float(service: FireflyService) -> None:
    result = await service.get_monthly_summary("2026-08")
    assert result["coverage"] == {"start": "2026-08-01", "end": "2026-08-31"}
    assert result["summary"]["balance-in"]["monetary_value"] == "1000.50"
    assert not isinstance(result["summary"]["balance-in"]["monetary_value"], float)


@pytest.mark.parametrize(
    ("start", "end", "message"),
    [
        ("2026-08-02", "2026-08-01", "before"),
        ("2025-01-01", "2026-08-30", "366"),
        ("not-a-date", "2026-08-30", "YYYY-MM-DD"),
    ],
)
@pytest.mark.asyncio
async def test_date_ranges_are_validated(service: FireflyService, start: str, end: str, message: str) -> None:
    with pytest.raises(InputError, match=message):
        await service.list_transactions(start=start, end=end)


@pytest.mark.asyncio
async def test_pagination_is_bounded(service: FireflyService) -> None:
    with pytest.raises(InputError, match="between 1 and 50"):
        await service.list_accounts(limit=51)


@pytest.mark.asyncio
async def test_search_query_is_bounded(service: FireflyService) -> None:
    with pytest.raises(InputError, match="empty"):
        await service.search_transactions(" ")
    with pytest.raises(InputError, match="500"):
        await service.search_transactions("x" * 501)


@pytest.mark.asyncio
async def test_unexpected_list_shape_is_rejected() -> None:
    client = FireflyClient(
        base_url="http://firefly.test/api/v1",
        token="secret",
        transport=httpx.MockTransport(lambda _request: httpx.Response(200, text='{"data":{"wrong":"shape"}}')),
    )
    service = FireflyService(client)
    with pytest.raises(ValueError, match="Unexpected Firefly III list response"):
        await service.list_accounts()
    await client.aclose()


@pytest.mark.asyncio
async def test_rule_list_minimizes_trigger_and_action_bodies(service: FireflyService) -> None:
    result = await service.list_rules()
    rule = result["rules"][0]
    assert "triggers" not in rule
    assert "actions" not in rule
    detail = await service.get_rule(12)
    assert detail["triggers"][0]["type"] == "description_contains"
    assert detail["actions"][0]["type"] == "set_category"


@pytest.mark.asyncio
async def test_exchange_rate_is_minimized_and_date_bounded(service: FireflyService) -> None:
    result = await service.get_exchange_rate("eur", "usd", "2026-08-30")
    assert result["pair"] == {"from": "EUR", "to": "USD"}
    assert result["rates"] == [
        {
            "from_currency_code": "EUR",
            "to_currency_code": "USD",
            "rate": "1.17000",
            "date": "2026-08-30T00:00:00+02:00",
        }
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "from_currency,to_currency,date_value", [("E!", "USD", None), ("EUR", "U$D", None), ("EUR", "USD", "bad-date")]
)
async def test_exchange_rate_rejects_invalid_inputs(
    service: FireflyService, from_currency: str, to_currency: str, date_value: str | None
) -> None:
    with pytest.raises(InputError):
        await service.get_exchange_rate(from_currency, to_currency, date_value)
