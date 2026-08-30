from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from firefly_iii_mcp.client import FireflyClient
from firefly_iii_mcp.service import FireflyService


def json_response(payload: Any, status: int = 200) -> httpx.Response:
    return httpx.Response(status, text=json.dumps(payload), headers={"Content-Type": "application/json"})


def detail_response(record: dict[str, Any]) -> httpx.Response:
    return json_response({"data": record})


def list_payload(
    items: list[dict[str, Any]], *, page: int = 1, per_page: int = 25, total: int | None = None
) -> dict[str, Any]:
    total = len(items) if total is None else total
    return {
        "data": items,
        "meta": {
            "pagination": {
                "current_page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": max(1, (total + per_page - 1) // per_page),
            }
        },
    }


def item(item_id: str, **attrs: Any) -> dict[str, Any]:
    return {"type": "example", "id": item_id, "attributes": attrs}


@pytest.fixture
def sample_transaction() -> dict[str, Any]:
    return item(
        "10",
        group_title=None,
        transactions=[
            {
                "transaction_journal_id": "101",
                "type": "withdrawal",
                "date": "2026-08-29T12:00:00+02:00",
                "amount": "12.34",
                "currency_code": "EUR",
                "description": "Example merchant",
                "source_id": "1",
                "source_name": "Current account",
                "destination_id": "2",
                "destination_name": "Groceries",
                "category_id": "3",
                "category_name": "Food",
                "tags": ["weekly"],
                "notes": "private note",
                "internal_reference": "must-not-leak",
            }
        ],
    )


@pytest.fixture
def api_handler(sample_transaction: dict[str, Any]) -> Callable[[httpx.Request], httpx.Response]:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/about"):
            return detail_response(
                item("0", version="6.6.6", api_version="2.1.0", php_version="8.4", os="Linux", driver="mysql")
            )
        if path.endswith("/accounts/1"):
            return detail_response(
                item(
                    "1",
                    name="Current account",
                    type="asset",
                    active=True,
                    current_balance="1000.50",
                    current_balance_date="2026-08-30T00:00:00+02:00",
                    currency_code="EUR",
                    currency_symbol="€",
                    include_net_worth=True,
                    account_role="defaultAsset",
                    liability_type=None,
                    liability_direction=None,
                    interest=None,
                    interest_period=None,
                    notes="private account note",
                )
            )
        if path.endswith("/accounts"):
            return json_response(
                list_payload(
                    [
                        item(
                            "1",
                            name="Current account",
                            type="asset",
                            active=True,
                            current_balance="1000.50",
                            current_balance_date="2026-08-30T00:00:00+02:00",
                            currency_code="EUR",
                            include_net_worth=True,
                            liability_type=None,
                            liability_direction=None,
                        )
                    ]
                )
            )
        if path.endswith("/transactions/10"):
            return detail_response(sample_transaction)
        if path.endswith("/transactions") and "/search/" not in path:
            return json_response(list_payload([sample_transaction]))
        if path.endswith("/search/transactions"):
            return json_response(list_payload([sample_transaction]))
        if path.endswith("/budget-limits"):
            return json_response(
                list_payload(
                    [
                        item(
                            "20",
                            budget_id="7",
                            start="2026-08-01T00:00:00+02:00",
                            end="2026-08-31T23:59:59+02:00",
                            amount="500.00",
                            currency_code="EUR",
                            spent=[{"currency_code": "EUR", "sum": "-125.25"}],
                        )
                    ]
                )
            )
        if path.endswith("/budgets"):
            return json_response(
                list_payload(
                    [item("7", name="Groceries", active=True, spent=[{"currency_code": "EUR", "sum": "-125.25"}])]
                )
            )
        if path.endswith("/bills"):
            return json_response(
                list_payload(
                    [
                        item(
                            "8",
                            name="Internet",
                            active=True,
                            currency_code="EUR",
                            amount_min="50.00",
                            amount_max="50.00",
                            repeat_freq="monthly",
                            next_expected_match="2026-09-05T00:00:00+02:00",
                            pay_dates=["2026-09-05"],
                            paid_dates=[],
                        )
                    ]
                )
            )
        if path.endswith("/categories"):
            return json_response(list_payload([item("3", name="Food", notes="hidden")]))
        if path.endswith("/tags"):
            return json_response(
                list_payload([item("4", tag="weekly", date="2026-01-01", description="Weekly spending")])
            )
        if path.endswith("/piggy-banks"):
            return json_response(
                list_payload(
                    [
                        item(
                            "5",
                            name="Emergency",
                            active=True,
                            current_amount="250.00",
                            target_amount="1000.00",
                            percentage=25,
                            currency_code="EUR",
                            notes="hidden",
                        )
                    ]
                )
            )
        if path.endswith("/recurrences"):
            return json_response(
                list_payload(
                    [
                        item(
                            "6",
                            type="withdrawal",
                            title="Rent",
                            description="Monthly rent",
                            active=True,
                            first_date="2026-01-01",
                            latest_date="2026-08-01",
                            repetitions=12,
                            notes="hidden",
                        )
                    ]
                )
            )
        if path.endswith("/currencies"):
            return json_response(
                list_payload(
                    [item("EUR", code="EUR", name="Euro", symbol="€", decimal_places=2, enabled=True, primary=True)]
                )
            )
        if path.endswith("/rule-groups/11"):
            return detail_response(
                item("11", title="Classification", description="Existing group", order=1, active=True)
            )
        if path.endswith("/rule-groups"):
            return json_response(
                list_payload([item("11", title="Classification", description="Existing group", order=1, active=True)])
            )
        if path.endswith("/rules/12"):
            return detail_response(
                item(
                    "12",
                    title="Groceries",
                    description="Classify grocery merchants",
                    rule_group_id="11",
                    rule_group_title="Classification",
                    order=1,
                    trigger="store-journal",
                    active=True,
                    strict=True,
                    stop_processing=False,
                    triggers=[{"type": "description_contains", "value": "market"}],
                    actions=[{"type": "set_category", "value": "Food"}],
                )
            )
        if path.endswith("/rules"):
            return json_response(
                list_payload(
                    [
                        item(
                            "12",
                            title="Groceries",
                            description="Classify grocery merchants",
                            rule_group_id="11",
                            rule_group_title="Classification",
                            order=1,
                            trigger="store-journal",
                            active=True,
                            strict=True,
                            stop_processing=False,
                            triggers=[{"type": "must-not-leak-in-list"}],
                            actions=[{"type": "must-not-leak-in-list"}],
                        )
                    ]
                )
            )
        if path.endswith("/exchange-rates/EUR/USD/2026-08-30") or path.endswith("/exchange-rates/EUR/USD"):
            return json_response(
                list_payload(
                    [
                        item(
                            "21",
                            from_currency_code="EUR",
                            to_currency_code="USD",
                            rate="1.17000",
                            date="2026-08-30T00:00:00+02:00",
                            from_currency_id="1",
                            to_currency_id="2",
                        )
                    ]
                )
            )
        if path.endswith("/summary/basic"):
            return httpx.Response(
                200,
                text='{"balance-in":{"key":"balance-in","title":"Balance","monetary_value":1000.50,"currency_code":"EUR"}}',
                headers={"Content-Type": "application/json"},
            )
        if path.endswith("/insight/expense/category"):
            return json_response([{"id": "3", "name": "Food", "difference": "-125.25", "currency_code": "EUR"}])
        if path.endswith("/insight/expense/total"):
            return json_response([{"difference": "-125.25", "currency_code": "EUR"}])
        if path.endswith("/insight/income/total"):
            return json_response([{"difference": "2500.00", "currency_code": "EUR"}])
        if path.endswith("/insight/transfer/total"):
            return json_response([{"difference": "300.00", "currency_code": "EUR"}])
        return json_response({"error": "not mocked"}, status=404)

    return handler


@pytest.fixture
async def service(api_handler: Callable[[httpx.Request], httpx.Response]) -> FireflyService:
    client = FireflyClient(
        base_url="http://firefly.test/api/v1", token="test-secret-token", transport=httpx.MockTransport(api_handler)
    )
    yield FireflyService(client)
    await client.aclose()
