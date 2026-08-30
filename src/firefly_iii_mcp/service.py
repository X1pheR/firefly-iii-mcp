from __future__ import annotations

import calendar
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from .client import Endpoint, FireflyClient

DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 50
MAX_DATE_RANGE_DAYS = 366
DEFAULT_TRANSACTION_DAYS = 30
MAX_LIST_ITEMS = 50


class InputError(ValueError):
    """Raised for invalid or unbounded user input before API access."""


def _page(page: int, limit: int) -> tuple[int, int]:
    if page < 1:
        raise InputError("page must be at least 1")
    if limit < 1 or limit > MAX_PAGE_SIZE:
        raise InputError(f"limit must be between 1 and {MAX_PAGE_SIZE}")
    return page, limit


def _parse_date(value: str | None, *, field: str) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise InputError(f"{field} must use YYYY-MM-DD") from exc


def _bounded_range(
    start: str | None,
    end: str | None,
    *,
    default_days: int | None = None,
) -> tuple[str | None, str | None]:
    end_date = _parse_date(end, field="end")
    start_date = _parse_date(start, field="start")
    if start_date is None and end_date is None and default_days is not None:
        end_date = date.today()
        start_date = end_date - timedelta(days=default_days - 1)
    elif start_date is None and end_date is not None and default_days is not None:
        start_date = end_date - timedelta(days=default_days - 1)
    elif start_date is not None and end_date is None:
        end_date = date.today()
    if start_date and end_date:
        if end_date < start_date:
            raise InputError("end must not be before start")
        if (end_date - start_date).days > MAX_DATE_RANGE_DAYS:
            raise InputError(f"date range must not exceed {MAX_DATE_RANGE_DAYS} days")
    return (start_date.isoformat() if start_date else None, end_date.isoformat() if end_date else None)


def _month_range(month: str | None) -> tuple[str, str, str]:
    if month is None:
        today = date.today()
        year, month_number = today.year, today.month
    else:
        try:
            parsed = date.fromisoformat(month + "-01")
        except ValueError as exc:
            raise InputError("month must use YYYY-MM") from exc
        year, month_number = parsed.year, parsed.month
    last_day = calendar.monthrange(year, month_number)[1]
    return (
        f"{year:04d}-{month_number:02d}",
        f"{year:04d}-{month_number:02d}-01",
        f"{year:04d}-{month_number:02d}-{last_day:02d}",
    )


def _unwrap_list(payload: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise ValueError("Unexpected Firefly III list response")
    rows: list[dict[str, Any]] = []
    for item in payload["data"]:
        if isinstance(item, dict):
            rows.append(item)
    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
    return rows, meta


def _unwrap_one(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
        raise ValueError("Unexpected Firefly III detail response")
    return payload["data"]


def _pagination(
    meta: dict[str, Any], *, returned: int, page: int | None = None, limit: int | None = None
) -> dict[str, Any]:
    source = meta.get("pagination") if isinstance(meta.get("pagination"), dict) else {}
    return {
        "returned": returned,
        "page": source.get("current_page", page),
        "per_page": source.get("per_page", limit),
        "total": source.get("total"),
        "total_pages": source.get("total_pages"),
    }


def _attrs(item: dict[str, Any]) -> dict[str, Any]:
    attrs = item.get("attributes")
    return attrs if isinstance(attrs, dict) else {}


def _money_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    result = []
    for entry in value:
        if not isinstance(entry, dict):
            continue
        result.append(
            {
                key: entry.get(key)
                for key in (
                    "currency_code",
                    "currency_symbol",
                    "currency_decimal_places",
                    "sum",
                    "amount",
                    "monetary_value",
                )
                if key in entry
            }
        )
    return result


def _decimal_or_none(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


class FireflyService:
    def __init__(self, client: FireflyClient) -> None:
        self.client = client

    async def get_about(self) -> dict[str, Any]:
        payload = await self.client.get(Endpoint.ABOUT)
        data = _unwrap_one(payload)
        attrs = _attrs(data)
        return {
            "version": attrs.get("version"),
            "api_version": attrs.get("api_version"),
            "php_version": attrs.get("php_version"),
            "os": attrs.get("os"),
            "driver": attrs.get("driver"),
        }

    async def list_accounts(
        self, account_type: str | None = None, page: int = 1, limit: int = DEFAULT_PAGE_SIZE
    ) -> dict[str, Any]:
        page, limit = _page(page, limit)
        payload = await self.client.get(Endpoint.ACCOUNTS, query={"type": account_type, "page": page, "limit": limit})
        items, meta = _unwrap_list(payload)
        accounts = []
        for item in items:
            a = _attrs(item)
            accounts.append(
                {
                    "id": item.get("id"),
                    "name": a.get("name"),
                    "type": a.get("type"),
                    "active": a.get("active"),
                    "current_balance": a.get("current_balance"),
                    "current_balance_date": a.get("current_balance_date"),
                    "currency_code": a.get("currency_code"),
                    "include_net_worth": a.get("include_net_worth"),
                    "liability_type": a.get("liability_type"),
                    "liability_direction": a.get("liability_direction"),
                }
            )
        return {"accounts": accounts, "pagination": _pagination(meta, returned=len(accounts), page=page, limit=limit)}

    async def get_account(self, account_id: int, include_notes: bool = False) -> dict[str, Any]:
        payload = await self.client.get(Endpoint.ACCOUNT, path_params={"id": account_id})
        item = _unwrap_one(payload)
        a = _attrs(item)
        result = {
            "id": item.get("id"),
            "name": a.get("name"),
            "type": a.get("type"),
            "active": a.get("active"),
            "current_balance": a.get("current_balance"),
            "current_balance_date": a.get("current_balance_date"),
            "currency_code": a.get("currency_code"),
            "currency_symbol": a.get("currency_symbol"),
            "include_net_worth": a.get("include_net_worth"),
            "account_role": a.get("account_role"),
            "liability_type": a.get("liability_type"),
            "liability_direction": a.get("liability_direction"),
            "interest": a.get("interest"),
            "interest_period": a.get("interest_period"),
        }
        if include_notes:
            result["notes"] = a.get("notes")
        return result

    def _transaction_item(self, item: dict[str, Any], *, include_notes: bool) -> dict[str, Any]:
        a = _attrs(item)
        splits = a.get("transactions") if isinstance(a.get("transactions"), list) else []
        minimized_splits = []
        for split in splits:
            if not isinstance(split, dict):
                continue
            row = {
                key: split.get(key)
                for key in (
                    "transaction_journal_id",
                    "type",
                    "date",
                    "amount",
                    "currency_code",
                    "foreign_amount",
                    "foreign_currency_code",
                    "description",
                    "source_id",
                    "source_name",
                    "destination_id",
                    "destination_name",
                    "budget_id",
                    "budget_name",
                    "category_id",
                    "category_name",
                    "bill_id",
                    "bill_name",
                    "tags",
                )
                if key in split
            }
            if include_notes and "notes" in split:
                row["notes"] = split.get("notes")
            minimized_splits.append(row)
        return {"id": item.get("id"), "group_title": a.get("group_title"), "transactions": minimized_splits}

    async def list_transactions(
        self,
        start: str | None = None,
        end: str | None = None,
        transaction_type: str | None = None,
        page: int = 1,
        limit: int = DEFAULT_PAGE_SIZE,
        include_notes: bool = False,
    ) -> dict[str, Any]:
        page, limit = _page(page, limit)
        start, end = _bounded_range(start, end, default_days=DEFAULT_TRANSACTION_DAYS)
        payload = await self.client.get(
            Endpoint.TRANSACTIONS,
            query={"start": start, "end": end, "type": transaction_type, "page": page, "limit": limit},
        )
        items, meta = _unwrap_list(payload)
        txs = [self._transaction_item(item, include_notes=include_notes) for item in items]
        return {
            "coverage": {"start": start, "end": end},
            "transactions": txs,
            "pagination": _pagination(meta, returned=len(txs), page=page, limit=limit),
        }

    async def get_transaction(self, transaction_id: int, include_notes: bool = False) -> dict[str, Any]:
        payload = await self.client.get(Endpoint.TRANSACTION, path_params={"id": transaction_id})
        return self._transaction_item(_unwrap_one(payload), include_notes=include_notes)

    async def search_transactions(
        self, query: str, page: int = 1, limit: int = DEFAULT_PAGE_SIZE, include_notes: bool = False
    ) -> dict[str, Any]:
        if not query.strip():
            raise InputError("query must not be empty")
        if len(query) > 500:
            raise InputError("query must not exceed 500 characters")
        page, limit = _page(page, limit)
        payload = await self.client.get(
            Endpoint.SEARCH_TRANSACTIONS, query={"query": query, "page": page, "limit": limit}
        )
        items, meta = _unwrap_list(payload)
        txs = [self._transaction_item(item, include_notes=include_notes) for item in items]
        return {"transactions": txs, "pagination": _pagination(meta, returned=len(txs), page=page, limit=limit)}

    async def list_budgets(
        self, start: str | None = None, end: str | None = None, page: int = 1, limit: int = DEFAULT_PAGE_SIZE
    ) -> dict[str, Any]:
        page, limit = _page(page, limit)
        start, end = _bounded_range(start, end, default_days=DEFAULT_TRANSACTION_DAYS)
        payload = await self.client.get(
            Endpoint.BUDGETS, query={"start": start, "end": end, "page": page, "limit": limit}
        )
        items, meta = _unwrap_list(payload)
        budgets = []
        for item in items:
            a = _attrs(item)
            budgets.append(
                {
                    "id": item.get("id"),
                    "name": a.get("name"),
                    "active": a.get("active"),
                    "spent": _money_list(a.get("spent")),
                }
            )
        return {
            "coverage": {"start": start, "end": end},
            "budgets": budgets,
            "pagination": _pagination(meta, returned=len(budgets), page=page, limit=limit),
        }

    async def get_budget_status(self, start: str | None = None, end: str | None = None) -> dict[str, Any]:
        start, end = _bounded_range(start, end, default_days=DEFAULT_TRANSACTION_DAYS)
        budgets_payload = await self.client.get(
            Endpoint.BUDGETS, query={"start": start, "end": end, "page": 1, "limit": MAX_LIST_ITEMS}
        )
        limits_payload = await self.client.get(Endpoint.BUDGET_LIMITS, query={"start": start, "end": end})
        budgets, _ = _unwrap_list(budgets_payload)
        limits, _ = _unwrap_list(limits_payload)
        limit_by_budget: dict[str, list[dict[str, Any]]] = {}
        for item in limits:
            a = _attrs(item)
            budget_id = str(a.get("budget_id"))
            amount = a.get("amount")
            spent_entries = _money_list(a.get("spent"))
            spent_by_currency = {str(x.get("currency_code")): x.get("sum", x.get("amount")) for x in spent_entries}
            currency = a.get("currency_code")
            spent = spent_by_currency.get(str(currency))
            amount_decimal = _decimal_or_none(amount)
            spent_decimal = _decimal_or_none(spent)
            remaining = None
            if amount_decimal is not None and spent_decimal is not None:
                remaining = format(amount_decimal - abs(spent_decimal), "f")
            limit_by_budget.setdefault(budget_id, []).append(
                {
                    "limit_id": item.get("id"),
                    "start": a.get("start"),
                    "end": a.get("end"),
                    "amount": amount,
                    "spent": spent,
                    "remaining": remaining,
                    "currency_code": currency,
                }
            )
        status = []
        for item in budgets[:MAX_LIST_ITEMS]:
            a = _attrs(item)
            status.append(
                {
                    "id": item.get("id"),
                    "name": a.get("name"),
                    "active": a.get("active"),
                    "spent": _money_list(a.get("spent")),
                    "limits": limit_by_budget.get(str(item.get("id")), []),
                }
            )
        return {
            "coverage": {"start": start, "end": end},
            "budgets": status,
            "returned": len(status),
            "max_returned": MAX_LIST_ITEMS,
        }

    async def list_bills(
        self, start: str | None = None, end: str | None = None, page: int = 1, limit: int = DEFAULT_PAGE_SIZE
    ) -> dict[str, Any]:
        page, limit = _page(page, limit)
        start, end = _bounded_range(start, end, default_days=DEFAULT_TRANSACTION_DAYS)
        payload = await self.client.get(
            Endpoint.BILLS, query={"start": start, "end": end, "page": page, "limit": limit}
        )
        items, meta = _unwrap_list(payload)
        bills = []
        for item in items:
            a = _attrs(item)
            bills.append(
                {
                    key: value
                    for key, value in {
                        "id": item.get("id"),
                        "name": a.get("name"),
                        "active": a.get("active"),
                        "currency_code": a.get("currency_code"),
                        "amount_min": a.get("amount_min"),
                        "amount_max": a.get("amount_max"),
                        "repeat_freq": a.get("repeat_freq"),
                        "next_expected_match": a.get("next_expected_match"),
                        "pay_dates": a.get("pay_dates"),
                        "paid_dates": a.get("paid_dates"),
                    }.items()
                    if value is not None
                }
            )
        return {
            "coverage": {"start": start, "end": end},
            "bills": bills,
            "pagination": _pagination(meta, returned=len(bills), page=page, limit=limit),
        }

    async def _simple_list(
        self, endpoint: Endpoint, key: str, page: int, limit: int, fields: tuple[str, ...]
    ) -> dict[str, Any]:
        page, limit = _page(page, limit)
        payload = await self.client.get(endpoint, query={"page": page, "limit": limit})
        items, meta = _unwrap_list(payload)
        result = []
        for item in items:
            a = _attrs(item)
            result.append({"id": item.get("id"), **{field: a.get(field) for field in fields if field in a}})
        return {key: result, "pagination": _pagination(meta, returned=len(result), page=page, limit=limit)}

    async def list_categories(self, page: int = 1, limit: int = DEFAULT_PAGE_SIZE) -> dict[str, Any]:
        return await self._simple_list(Endpoint.CATEGORIES, "categories", page, limit, ("name",))

    async def list_tags(self, page: int = 1, limit: int = DEFAULT_PAGE_SIZE) -> dict[str, Any]:
        return await self._simple_list(Endpoint.TAGS, "tags", page, limit, ("tag", "date", "description"))

    async def list_piggy_banks(self, page: int = 1, limit: int = DEFAULT_PAGE_SIZE) -> dict[str, Any]:
        return await self._simple_list(
            Endpoint.PIGGY_BANKS,
            "piggy_banks",
            page,
            limit,
            ("name", "active", "current_amount", "target_amount", "percentage", "currency_code"),
        )

    async def list_recurrences(self, page: int = 1, limit: int = DEFAULT_PAGE_SIZE) -> dict[str, Any]:
        return await self._simple_list(
            Endpoint.RECURRENCES,
            "recurrences",
            page,
            limit,
            ("type", "title", "description", "active", "first_date", "latest_date", "repetitions"),
        )

    async def list_currencies(self, page: int = 1, limit: int = DEFAULT_PAGE_SIZE) -> dict[str, Any]:
        return await self._simple_list(
            Endpoint.CURRENCIES,
            "currencies",
            page,
            limit,
            ("code", "name", "symbol", "decimal_places", "enabled", "primary"),
        )

    async def list_rule_groups(self, page: int = 1, limit: int = DEFAULT_PAGE_SIZE) -> dict[str, Any]:
        return await self._simple_list(
            Endpoint.RULE_GROUPS,
            "rule_groups",
            page,
            limit,
            ("title", "description", "order", "active"),
        )

    async def get_rule_group(self, rule_group_id: int) -> dict[str, Any]:
        payload = await self.client.get(Endpoint.RULE_GROUP, path_params={"id": rule_group_id})
        item = _unwrap_one(payload)
        a = _attrs(item)
        return {
            "id": item.get("id"),
            "title": a.get("title"),
            "description": a.get("description"),
            "order": a.get("order"),
            "active": a.get("active"),
        }

    async def list_rules(self, page: int = 1, limit: int = DEFAULT_PAGE_SIZE) -> dict[str, Any]:
        return await self._simple_list(
            Endpoint.RULES,
            "rules",
            page,
            limit,
            (
                "title",
                "description",
                "rule_group_id",
                "rule_group_title",
                "order",
                "trigger",
                "active",
                "strict",
                "stop_processing",
            ),
        )

    async def get_rule(self, rule_id: int) -> dict[str, Any]:
        payload = await self.client.get(Endpoint.RULE, path_params={"id": rule_id})
        item = _unwrap_one(payload)
        a = _attrs(item)
        return {
            key: value
            for key, value in {
                "id": item.get("id"),
                "title": a.get("title"),
                "description": a.get("description"),
                "rule_group_id": a.get("rule_group_id"),
                "rule_group_title": a.get("rule_group_title"),
                "order": a.get("order"),
                "trigger": a.get("trigger"),
                "active": a.get("active"),
                "strict": a.get("strict"),
                "stop_processing": a.get("stop_processing"),
                "triggers": a.get("triggers"),
                "actions": a.get("actions"),
            }.items()
            if value is not None
        }

    async def get_exchange_rate(
        self, from_currency: str, to_currency: str, rate_date: str | None = None
    ) -> dict[str, Any]:
        from_code = from_currency.strip().upper()
        to_code = to_currency.strip().upper()
        if not (3 <= len(from_code) <= 12 and from_code.isalnum()):
            raise InputError("from_currency must be an alphanumeric currency code")
        if not (3 <= len(to_code) <= 12 and to_code.isalnum()):
            raise InputError("to_currency must be an alphanumeric currency code")
        path_params: dict[str, str] = {"from": from_code, "to": to_code}
        endpoint = Endpoint.EXCHANGE_RATES
        if rate_date is not None:
            parsed = _parse_date(rate_date, field="date")
            if parsed is None:
                raise InputError("date must use YYYY-MM-DD")
            path_params["date"] = parsed.isoformat()
            endpoint = Endpoint.EXCHANGE_RATE_ON_DATE
        payload = await self.client.get(endpoint, path_params=path_params, query={"page": 1, "limit": MAX_PAGE_SIZE})
        items, meta = _unwrap_list(payload)
        rates = []
        for item in items[:MAX_PAGE_SIZE]:
            a = _attrs(item)
            rates.append(
                {
                    "from_currency_code": a.get("from_currency_code"),
                    "to_currency_code": a.get("to_currency_code"),
                    "rate": a.get("rate"),
                    "date": a.get("date"),
                }
            )
        return {
            "pair": {"from": from_code, "to": to_code},
            "date": rate_date,
            "rates": rates,
            "pagination": _pagination(meta, returned=len(rates), page=1, limit=MAX_PAGE_SIZE),
        }

    async def get_cashflow(self, start: str | None = None, end: str | None = None) -> dict[str, Any]:
        start, end = _bounded_range(start, end, default_days=DEFAULT_TRANSACTION_DAYS)
        query = {"start": start, "end": end}
        expense = await self.client.get(Endpoint.INSIGHT_EXPENSE_TOTAL, query=query)
        income = await self.client.get(Endpoint.INSIGHT_INCOME_TOTAL, query=query)
        transfers = await self.client.get(Endpoint.INSIGHT_TRANSFER_TOTAL, query=query)
        return {"coverage": {"start": start, "end": end}, "expense": expense, "income": income, "transfers": transfers}

    async def get_spending_by_category(
        self, start: str | None = None, end: str | None = None, category_ids: list[int] | None = None
    ) -> dict[str, Any]:
        start, end = _bounded_range(start, end, default_days=DEFAULT_TRANSACTION_DAYS)
        if category_ids and len(category_ids) > 20:
            raise InputError("at most 20 category_ids may be supplied")
        payload = await self.client.get(
            Endpoint.INSIGHT_EXPENSE_CATEGORY,
            query={"start": start, "end": end, "categories[]": category_ids or None},
        )
        return {"coverage": {"start": start, "end": end}, "categories": payload}

    async def get_monthly_summary(self, month: str | None = None, currency_code: str | None = None) -> dict[str, Any]:
        month_key, start, end = _month_range(month)
        query = {"start": start, "end": end}
        summary = await self.client.get(Endpoint.SUMMARY_BASIC, query={**query, "currency_code": currency_code})
        expense = await self.client.get(Endpoint.INSIGHT_EXPENSE_TOTAL, query=query)
        income = await self.client.get(Endpoint.INSIGHT_INCOME_TOTAL, query=query)
        return {
            "month": month_key,
            "coverage": {"start": start, "end": end},
            "summary": summary,
            "expense": expense,
            "income": income,
        }
