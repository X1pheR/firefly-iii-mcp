# Security Policy

## Supported versions

Security fixes are provided for the latest released version of Firefly III MCP.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use [GitHub Private Vulnerability Reporting](https://github.com/X1pheR/firefly-iii-mcp/security/advisories/new) for this repository when available. If that channel is unavailable, contact the maintainer privately through the GitHub profile associated with this repository.

Do not include real Firefly III Personal Access Tokens, passwords, transaction exports or other private financial data in a report.

## Financial-data boundary

This server treats Firefly III data as sensitive personal financial data. It is intended for a trusted authenticated MCP deployment and must not be exposed as an unauthenticated public MCP endpoint.

## Credential model

Firefly III v6.6.6 Personal Access Tokens do not provide a useful read-only scope boundary. A dedicated MCP PAT therefore retains the authority of its Firefly III user and must be handled as a broad financial credential.

The runtime reads the credential only from `FIREFLY_TOKEN_FILE`. Never pass the token through Git-tracked configuration, MCP arguments, command-line arguments, documentation, logs or routine diagnostics.

In the Hypershell deployment the credential is owned by Bitwarden Secrets Manager, rendered by Secrets Delivery Manager to a private runtime file, and exposed only to the MCPJungle child process that needs it.

If a PAT is exposed, revoke it in Firefly III and create a replacement. Do not reuse a credential that may have been disclosed.

## Read-only enforcement

The implementation contains no API endpoints or MCP tools for account/transaction/budget/bill/category/tag/piggy-bank/recurrence/rule/currency mutation, rule execution, attachment download or mutation, exports, data import/destruction/purge, webhooks, cron/automation triggers, preferences/user configuration, credential administration, or arbitrary HTTP methods/paths.

The HTTP client rejects any method other than `GET` before network I/O and accepts only a fixed reviewed endpoint allowlist. Representative write attempts are tested safely at both the MCP inventory boundary and the internal client boundary without issuing a mutating request to Firefly III.

## Data minimization

Tool handlers project Firefly responses into bounded purpose-specific structures instead of exposing arbitrary API objects. Pagination and date ranges are bounded; notes are omitted by default; API error bodies are not returned; bearer credentials and request details are never included in sanitized errors.
