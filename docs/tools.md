# Tool reference

Firefly III MCP v0.1.1 exposes exactly 22 explicit read-only tools. There is no generic HTTP/API passthrough.

| Tool | Access | Destructive | Purpose / bounded output |
|---|---|---:|---|
| `firefly_get_about` | Read | No | Returns Firefly III/API version, PHP version, OS and database driver. |
| `firefly_list_accounts` | Read | No | Lists accounts with bounded pagination and minimized balance/type metadata. |
| `firefly_get_account` | Read | No | Gets one account. Notes are excluded unless `include_notes=true`. |
| `firefly_list_transactions` | Read | No | Lists minimized transaction groups; defaults to 30 days, max 366-day range, max 50/page. |
| `firefly_get_transaction` | Read | No | Gets one minimized transaction group. Notes are excluded unless requested. |
| `firefly_search_transactions` | Read | No | Searches with Firefly search syntax; query length and pagination are bounded. |
| `firefly_list_budgets` | Read | No | Lists budgets and official spent values for a bounded period. |
| `firefly_get_budget_status` | Read | No | Combines budgets and limits into spent/remaining status for a bounded period. |
| `firefly_list_bills` | Read | No | Lists recurring obligations and expected/paid timing for a bounded period. |
| `firefly_list_categories` | Read | No | Lists category IDs/names with bounded pagination; notes are excluded. |
| `firefly_list_tags` | Read | No | Lists tag metadata with bounded pagination. |
| `firefly_list_piggy_banks` | Read | No | Lists savings goals with current/target amounts and percentage. |
| `firefly_list_recurrences` | Read | No | Lists recurrence definitions without execution or mutation capability. |
| `firefly_list_currencies` | Read | No | Lists configured currency identity/decimal metadata. |
| `firefly_list_rule_groups` | Read | No | Lists rule-group metadata without rule execution. |
| `firefly_get_rule_group` | Read | No | Gets one rule-group definition. |
| `firefly_list_rules` | Read | No | Lists rule metadata while excluding full trigger/action bodies. |
| `firefly_get_rule` | Read | No | Gets one existing rule including triggers/actions for inspection only; never executes it. |
| `firefly_get_exchange_rate` | Read | No | Gets configured rates for one currency pair, optionally on one date. |
| `firefly_get_cashflow` | Read | No | Returns official income, expense and transfer insight totals for a bounded period. |
| `firefly_get_spending_by_category` | Read | No | Returns official expense insight by category; at most 20 category IDs may be supplied. |
| `firefly_get_monthly_summary` | Read | No | Returns one calendar month's official summary, expense and income data. |

## Shared bounds

- List page size: 1–50 records.
- Transaction/date range: at most 366 days.
- Default transaction-oriented range: 30 days.
- Search text: non-empty, at most 500 characters.
- Category filter: at most 20 IDs.
- Currency-pair inputs: normalized uppercase alphanumeric codes.
- Notes: excluded by default and available only on the supported account/transaction detail reads.

## MCP annotations

Every tool publishes:

- `readOnlyHint=true`
- `destructiveHint=false`
- `idempotentHint=true`
- `openWorldHint=true`

`openWorldHint=true` reflects authenticated reads from the external Firefly III application; it does not grant or imply mutation capability.

## HTTP enforcement boundary

The internal client rejects every HTTP method except `GET` before network I/O and accepts only the reviewed Firefly III endpoint set used by these tools. Tool inputs cannot supply a raw URL, arbitrary path or method.

The Personal Access Token itself is broader than this MCP surface because Firefly III 6.6.6 has no useful read-only PAT scope. Deployments must therefore treat the PAT as a sensitive financial credential even though every exposed MCP operation is read-only.

## Intentionally unavailable

These capabilities are absent from the MCP registry rather than merely discouraged:

- account, transaction, budget, bill, category, tag, piggy-bank, recurrence, currency or rule mutation;
- rule test/execute actions;
- attachments and exports;
- data import, purge or destructive maintenance;
- webhooks, cron or other automation triggers;
- preferences, user or system administration;
- PAT/OAuth credential administration;
- generic HTTP/API requests.
