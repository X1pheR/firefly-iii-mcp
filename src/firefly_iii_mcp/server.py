from __future__ import annotations

from fastmcp import FastMCP

from .service import FireflyService

TOOL_NAMES = (
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
)

READ_ONLY_ANNOTATIONS = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}


def create_mcp(service: FireflyService) -> FastMCP:
    mcp = FastMCP(
        name="Hypershell Firefly III Read-Only",
        instructions=(
            "Read-only semantic access to Firefly III. The server exposes only an explicit GET endpoint allowlist; "
            "Financial mutations, imports, exports, attachments, automation and arbitrary API requests "
            "are not available."
        ),
    )

    @mcp.tool(name="firefly_get_about", annotations=READ_ONLY_ANNOTATIONS)
    async def get_about() -> dict:
        """Return Firefly III application/API version information."""
        return await service.get_about()

    @mcp.tool(name="firefly_list_accounts", annotations=READ_ONLY_ANNOTATIONS)
    async def list_accounts(account_type: str | None = None, page: int = 1, limit: int = 25) -> dict:
        """List financial accounts with balances and minimal metadata."""
        return await service.list_accounts(account_type=account_type, page=page, limit=limit)

    @mcp.tool(name="firefly_get_account", annotations=READ_ONLY_ANNOTATIONS)
    async def get_account(account_id: int, include_notes: bool = False) -> dict:
        """Get one account by numeric ID; notes are excluded unless explicitly requested."""
        return await service.get_account(account_id=account_id, include_notes=include_notes)

    @mcp.tool(name="firefly_list_transactions", annotations=READ_ONLY_ANNOTATIONS)
    async def list_transactions(
        start: str | None = None,
        end: str | None = None,
        transaction_type: str | None = None,
        page: int = 1,
        limit: int = 25,
        include_notes: bool = False,
    ) -> dict:
        """List bounded transactions; defaults to the last 30 days and excludes notes unless requested."""
        return await service.list_transactions(start, end, transaction_type, page, limit, include_notes)

    @mcp.tool(name="firefly_get_transaction", annotations=READ_ONLY_ANNOTATIONS)
    async def get_transaction(transaction_id: int, include_notes: bool = False) -> dict:
        """Get one transaction group by numeric ID with minimized split fields."""
        return await service.get_transaction(transaction_id, include_notes)

    @mcp.tool(name="firefly_search_transactions", annotations=READ_ONLY_ANNOTATIONS)
    async def search_transactions(query: str, page: int = 1, limit: int = 25, include_notes: bool = False) -> dict:
        """Search transactions using Firefly III search syntax with bounded result pagination."""
        return await service.search_transactions(query, page, limit, include_notes)

    @mcp.tool(name="firefly_list_budgets", annotations=READ_ONLY_ANNOTATIONS)
    async def list_budgets(start: str | None = None, end: str | None = None, page: int = 1, limit: int = 25) -> dict:
        """List budgets and spending for a bounded period."""
        return await service.list_budgets(start, end, page, limit)

    @mcp.tool(name="firefly_get_budget_status", annotations=READ_ONLY_ANNOTATIONS)
    async def get_budget_status(start: str | None = None, end: str | None = None) -> dict:
        """Return budget limits, spending and remaining amounts for a bounded period."""
        return await service.get_budget_status(start, end)

    @mcp.tool(name="firefly_list_bills", annotations=READ_ONLY_ANNOTATIONS)
    async def list_bills(start: str | None = None, end: str | None = None, page: int = 1, limit: int = 25) -> dict:
        """List bills/recurring obligations and expected payment timing for a bounded period."""
        return await service.list_bills(start, end, page, limit)

    @mcp.tool(name="firefly_list_categories", annotations=READ_ONLY_ANNOTATIONS)
    async def list_categories(page: int = 1, limit: int = 25) -> dict:
        """List transaction categories without notes."""
        return await service.list_categories(page, limit)

    @mcp.tool(name="firefly_list_tags", annotations=READ_ONLY_ANNOTATIONS)
    async def list_tags(page: int = 1, limit: int = 25) -> dict:
        """List tags with bounded pagination."""
        return await service.list_tags(page, limit)

    @mcp.tool(name="firefly_list_piggy_banks", annotations=READ_ONLY_ANNOTATIONS)
    async def list_piggy_banks(page: int = 1, limit: int = 25) -> dict:
        """List savings goals with current and target amounts."""
        return await service.list_piggy_banks(page, limit)

    @mcp.tool(name="firefly_list_recurrences", annotations=READ_ONLY_ANNOTATIONS)
    async def list_recurrences(page: int = 1, limit: int = 25) -> dict:
        """List recurring transaction definitions without mutation or execution capabilities."""
        return await service.list_recurrences(page, limit)

    @mcp.tool(name="firefly_list_currencies", annotations=READ_ONLY_ANNOTATIONS)
    async def list_currencies(page: int = 1, limit: int = 25) -> dict:
        """List configured currencies and decimal metadata."""
        return await service.list_currencies(page, limit)

    @mcp.tool(name="firefly_list_rule_groups", annotations=READ_ONLY_ANNOTATIONS)
    async def list_rule_groups(page: int = 1, limit: int = 25) -> dict:
        """List existing Firefly III rule groups without executing or modifying them."""
        return await service.list_rule_groups(page, limit)

    @mcp.tool(name="firefly_get_rule_group", annotations=READ_ONLY_ANNOTATIONS)
    async def get_rule_group(rule_group_id: int) -> dict:
        """Get one existing rule group by numeric ID without its rule bodies."""
        return await service.get_rule_group(rule_group_id)

    @mcp.tool(name="firefly_list_rules", annotations=READ_ONLY_ANNOTATIONS)
    async def list_rules(page: int = 1, limit: int = 25) -> dict:
        """List rule metadata without executing rules or returning full trigger/action bodies."""
        return await service.list_rules(page, limit)

    @mcp.tool(name="firefly_get_rule", annotations=READ_ONLY_ANNOTATIONS)
    async def get_rule(rule_id: int) -> dict:
        """Get one rule definition including its existing triggers and actions; never execute it."""
        return await service.get_rule(rule_id)

    @mcp.tool(name="firefly_get_exchange_rate", annotations=READ_ONLY_ANNOTATIONS)
    async def get_exchange_rate(from_currency: str, to_currency: str, date: str | None = None) -> dict:
        """Get configured exchange rates for a currency pair, optionally on one YYYY-MM-DD date."""
        return await service.get_exchange_rate(from_currency, to_currency, date)

    @mcp.tool(name="firefly_get_cashflow", annotations=READ_ONLY_ANNOTATIONS)
    async def get_cashflow(start: str | None = None, end: str | None = None) -> dict:
        """Return official income, expense and transfer totals for a bounded period."""
        return await service.get_cashflow(start, end)

    @mcp.tool(name="firefly_get_spending_by_category", annotations=READ_ONLY_ANNOTATIONS)
    async def get_spending_by_category(
        start: str | None = None,
        end: str | None = None,
        category_ids: list[int] | None = None,
    ) -> dict:
        """Return official expense insight grouped by category for a bounded period."""
        return await service.get_spending_by_category(start, end, category_ids)

    @mcp.tool(name="firefly_get_monthly_summary", annotations=READ_ONLY_ANNOTATIONS)
    async def get_monthly_summary(month: str | None = None, currency_code: str | None = None) -> dict:
        """Return a monthly financial summary using official summary and insight endpoints."""
        return await service.get_monthly_summary(month, currency_code)

    return mcp
