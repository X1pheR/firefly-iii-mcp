# Hypershell Firefly III MCP

A deliberately small, strictly read-only Model Context Protocol (MCP) adapter for Firefly III.

Current general-purpose Firefly III MCP servers expose broad CRUD/action surfaces or filtering mechanisms that do not meet Hypershell's financial-data safety boundary. This project intentionally implements a compact semantic read surface instead of generating the complete Firefly III OpenAPI specification.

## Compatibility baseline

- Firefly III: `v6.6.6`
- Firefly III source revision: `a95b82b14cb01b6e40491f2a94c53b47b71766e7`
- Firefly III API docs branch: `v6.6.6`
- Firefly III API docs revision: `fe6e96739ea9056c09d45e4fce1d471af23a2891`
- MCP runtime: FastMCP `3.4.7`, stdio only

Firefly III Personal Access Tokens are user-authority bearer credentials. Firefly III v6.6.6 does not define useful PAT/OAuth API scopes or a read-only API role for this use case. The token itself is therefore **not read-only**. The MCP server is the primary technical enforcement boundary.

## Safety model

1. Exactly 22 explicit semantic MCP tools are registered.
2. The API client has a fixed 25-endpoint allowlist.
3. The client rejects any HTTP method other than `GET` before network I/O.
4. No MCP input accepts an arbitrary HTTP method or path.
5. There are no mutation, import, export, attachment, rule-execution, webhook, cron or automation tools.
6. List pagination is bounded to at most 50 records per page.
7. Transaction/date-oriented reads default to a 30-day window and reject ranges over 366 days.
8. Notes are omitted unless explicitly requested by a detail/read tool.
9. JSON decimal numbers are parsed through `Decimal` and serialized as strings.
10. API errors are sanitized and never include bearer tokens, response bodies or query contents.
11. The token is accepted only through a private file path (`FIREFLY_TOKEN_FILE`).

## Published tools

- `firefly_get_about`
- `firefly_list_accounts`
- `firefly_get_account`
- `firefly_list_transactions`
- `firefly_get_transaction`
- `firefly_search_transactions`
- `firefly_list_budgets`
- `firefly_get_budget_status`
- `firefly_list_bills`
- `firefly_list_categories`
- `firefly_list_tags`
- `firefly_list_piggy_banks`
- `firefly_list_recurrences`
- `firefly_list_currencies`
- `firefly_list_rule_groups`
- `firefly_get_rule_group`
- `firefly_list_rules`
- `firefly_get_rule`
- `firefly_get_exchange_rate`
- `firefly_get_cashflow`
- `firefly_get_spending_by_category`
- `firefly_get_monthly_summary`

## Runtime configuration

```text
FIREFLY_BASE_URL=http://firefly_core:8080/api/v1
FIREFLY_TOKEN_FILE=/absolute/path/to/private/token-file
```

`FIREFLY_TOKEN_FILE` must be absolute and must not be group/world accessible. The token value must never be committed to Git, written to documentation, emitted in logs or supplied as an MCP argument.

## Development

```bash
uv sync --all-groups
./scripts/verify.sh
```
