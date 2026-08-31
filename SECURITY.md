# Security Policy

## Supported versions

Security fixes are provided for the latest released version of Firefly III MCP.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use [GitHub Private Vulnerability Reporting](https://github.com/X1pheR/firefly-iii-mcp/security/advisories/new) when available. If that channel is unavailable, contact the maintainer privately through the [GitHub profile associated with this repository](https://github.com/X1pheR).

A useful report should include the affected version or commit, the relevant tool/configuration boundary, reproduction steps that do not contain real financial data or credentials, the expected impact, and any suggested mitigation.

Do not include real Firefly III Personal Access Tokens, passwords, transaction exports or other private financial data in a report.

The maintainer aims to acknowledge a private vulnerability report within 14 days. Confirmed vulnerabilities are prioritized according to severity and exploitability; publicly disclosed vulnerabilities of medium or higher severity should normally be fixed or explicitly mitigated within 60 days.

## Coordinated disclosure

Please keep an undisclosed vulnerability private until a fix or mitigation is available. When a release fixes a publicly known vulnerability, the release notes will identify the security impact and affected versions where doing so does not increase risk to users who have not yet upgraded.

## Financial-data boundary

This server treats Firefly III data as sensitive personal financial data. It is a local stdio MCP process intended for trusted MCP clients or gateways; it must not be wrapped in an unauthenticated public network endpoint.

## Credential model

Firefly III v6.6.6 Personal Access Tokens do not provide a useful read-only scope boundary. A dedicated MCP PAT therefore retains the authority of its Firefly III user and must be handled as a broad financial credential.

The runtime reads the credential only from `FIREFLY_TOKEN_FILE`. Never pass the token through Git-tracked configuration, MCP arguments, command-line arguments, documentation, logs or routine diagnostics. The credential file must be a private regular file and the process should receive no credentials beyond those required for Firefly access.

If a PAT is exposed, revoke it in Firefly III and create a replacement. Do not reuse a credential that may have been disclosed.

## Read-only enforcement

The implementation contains no API endpoints or MCP tools for account/transaction/budget/bill/category/tag/piggy-bank/recurrence/rule/currency mutation, rule execution, attachment download or mutation, exports, data import/destruction/purge, webhooks, cron/automation triggers, preferences/user configuration, credential administration, or arbitrary HTTP methods/paths.

The HTTP client rejects any method other than `GET` before network I/O and accepts only a fixed reviewed endpoint allowlist. Representative write attempts are tested safely at both the MCP inventory boundary and the internal client boundary without issuing a mutating request to Firefly III.

## Data minimization

Tool handlers project Firefly responses into bounded purpose-specific structures instead of exposing arbitrary API objects. Pagination and date ranges are bounded; notes are omitted by default; API error bodies are not returned; bearer credentials and request details are never included in sanitized errors.

## Public build and supply-chain boundary

Public GitHub workflows must not receive Firefly credentials or production Homelab credentials. CI uses synthetic fixtures only. Dependency updates are lockfile-reviewed, GitHub Actions are commit-pinned, CodeQL and OpenSSF Scorecard are enabled for the public repository, and release artifacts are built from an exact accepted tag with checksums and GitHub/Sigstore provenance.
