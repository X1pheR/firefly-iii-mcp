# Security model

## Financial-data boundary

This server treats Firefly III data as sensitive personal financial data. It is designed for a trusted internal MCPJungle deployment and must not be exposed as a raw public MCP endpoint.

## Credential model

Firefly III v6.6.6 Personal Access Tokens do not provide a useful read-only scope boundary. A dedicated MCP PAT therefore retains the authority of its Firefly III user and must be handled as a broad financial credential.

Production delivery must use Hypershell's governed Bitwarden Secrets Manager to Secrets Delivery Manager path. The MCP runtime receives only a private token file. Never pass the token via Git-tracked configuration, CLI arguments, documentation, logs, HATS state or routine low-trust tool surfaces.

## Enforced exclusions

The implementation contains no API endpoints or MCP tools for transaction/account/budget/bill/category/tag/piggy-bank/recurrence/rule/currency mutation, rule execution, attachment download or mutation, exports, data import/destruction/purge, webhooks, cron/automation triggers, preferences/user configuration, or arbitrary HTTP methods/paths.

A representative write attempt is tested at both the MCP inventory boundary and the internal HTTP client boundary without issuing a mutating request to Firefly III.
