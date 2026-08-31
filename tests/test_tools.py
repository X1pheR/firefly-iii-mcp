from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastmcp import Client

from firefly_iii_mcp.server import TOOL_NAMES, create_mcp
from firefly_iii_mcp.service import FireflyService

EXPECTED_TOOLS = {
    "firefly_get_about",
    "firefly_list_accounts",
    "firefly_get_account",
    "firefly_list_transactions",
    "firefly_get_transaction",
    "firefly_search_transactions",
    "firefly_list_budgets",
    "firefly_get_budget_status",
    "firefly_list_bills",
    "firefly_list_categories",
    "firefly_list_tags",
    "firefly_list_piggy_banks",
    "firefly_list_recurrences",
    "firefly_list_currencies",
    "firefly_list_rule_groups",
    "firefly_get_rule_group",
    "firefly_list_rules",
    "firefly_get_rule",
    "firefly_get_exchange_rate",
    "firefly_get_cashflow",
    "firefly_get_spending_by_category",
    "firefly_get_monthly_summary",
}
ROOT = Path(__file__).parents[1]

WRITE_TOKENS = {
    "create",
    "update",
    "delete",
    "store",
    "upload",
    "import",
    "trigger",
    "execute",
    "request",
    "export",
    "purge",
    "destroy",
}


def test_tool_reference_covers_exact_published_inventory() -> None:
    reference = (ROOT / "docs/tools.md").read_text(encoding="utf-8")
    documented = {name for name in TOOL_NAMES if f"`{name}`" in reference}
    assert documented == set(TOOL_NAMES)
    assert "exactly 22 explicit read-only tools" in reference


def test_build_vs_reuse_decision_is_documented() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    alternatives = (ROOT / "docs/alternatives.md").read_text(encoding="utf-8")
    alternatives_lower = alternatives.lower()

    assert "docs/alternatives.md" in readme
    assert "not simply that existing servers could write" in readme
    assert "daften/fireflyiii-mcp" in alternatives
    assert "read-only mode was not enough" in alternatives_lower
    assert "semantic agent tools" in alternatives_lower
    assert "data minimization" in alternatives_lower
    assert "when reuse should be reconsidered" in alternatives_lower


@pytest.mark.asyncio
async def test_exact_effective_tool_inventory(service: FireflyService) -> None:
    mcp = create_mcp(service)
    async with Client(mcp) as client:
        tools = await client.list_tools()
    names = {tool.name for tool in tools}
    assert names == EXPECTED_TOOLS == set(TOOL_NAMES)
    assert len(names) == 22
    for name in names:
        assert not any(token in name for token in WRITE_TOKENS)


@pytest.mark.asyncio
async def test_every_published_tool_executes_against_mocked_read_api(service: FireflyService) -> None:
    calls = {
        "firefly_get_about": {},
        "firefly_list_accounts": {},
        "firefly_get_account": {"account_id": 1},
        "firefly_list_transactions": {"start": "2026-08-01", "end": "2026-08-31"},
        "firefly_get_transaction": {"transaction_id": 10},
        "firefly_search_transactions": {"query": "example"},
        "firefly_list_budgets": {"start": "2026-08-01", "end": "2026-08-31"},
        "firefly_get_budget_status": {"start": "2026-08-01", "end": "2026-08-31"},
        "firefly_list_bills": {"start": "2026-08-01", "end": "2026-08-31"},
        "firefly_list_categories": {},
        "firefly_list_tags": {},
        "firefly_list_piggy_banks": {},
        "firefly_list_recurrences": {},
        "firefly_list_currencies": {},
        "firefly_list_rule_groups": {},
        "firefly_get_rule_group": {"rule_group_id": 11},
        "firefly_list_rules": {},
        "firefly_get_rule": {"rule_id": 12},
        "firefly_get_exchange_rate": {"from_currency": "EUR", "to_currency": "USD", "date": "2026-08-30"},
        "firefly_get_cashflow": {"start": "2026-08-01", "end": "2026-08-31"},
        "firefly_get_spending_by_category": {"start": "2026-08-01", "end": "2026-08-31"},
        "firefly_get_monthly_summary": {"month": "2026-08"},
    }
    mcp = create_mcp(service)
    async with Client(mcp) as client:
        for name, args in calls.items():
            result = await client.call_tool(name, args)
            assert not result.is_error, name
            assert result.content, name


@pytest.mark.asyncio
async def test_representative_write_call_is_absent_at_mcp_boundary(service: FireflyService) -> None:
    mcp = create_mcp(service)
    async with Client(mcp) as client:
        result = await client.call_tool("firefly_create_transaction", {"amount": "1.00"}, raise_on_error=False)
    assert result.is_error


@pytest.mark.asyncio
async def test_tools_have_read_only_annotations(service: FireflyService) -> None:
    mcp = create_mcp(service)
    async with Client(mcp) as client:
        tools = await client.list_tools()
    for tool in tools:
        annotations = json.loads(tool.annotations.model_dump_json()) if tool.annotations else {}
        assert annotations.get("readOnlyHint") is True
        assert annotations.get("destructiveHint") is False
        assert annotations.get("idempotentHint") is True
        assert annotations.get("openWorldHint") is True
