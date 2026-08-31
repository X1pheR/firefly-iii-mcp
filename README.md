# Firefly III MCP

[![CI](https://github.com/X1pheR/firefly-iii-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/X1pheR/firefly-iii-mcp/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/X1pheR/firefly-iii-mcp/badge)](https://scorecard.dev/viewer/?uri=github.com/X1pheR/firefly-iii-mcp)
[![GitHub Release](https://img.shields.io/github/v/release/X1pheR/firefly-iii-mcp)](https://github.com/X1pheR/firefly-iii-mcp/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.12-3.14](https://img.shields.io/badge/python-3.12--3.14-blue.svg)](pyproject.toml)
[![Firefly III 6.6.6](https://img.shields.io/badge/tested%20with-Firefly%20III%206.6.6-orange.svg)](https://github.com/firefly-iii/firefly-iii/releases/tag/v6.6.6)

`firefly-iii-mcp` is a Hypershell-maintained Model Context Protocol (MCP) server for strictly read-only, bounded access to [Firefly III](https://github.com/firefly-iii/firefly-iii). It is an independent community integration and is not affiliated with, endorsed by, or maintained by the Firefly III project.

The server intentionally exposes a small semantic financial-analysis surface instead of generating or proxying the complete Firefly III API. This keeps mutations, automation and arbitrary HTTP access absent from the MCP contract.

## Feedback and contributions

Use [GitHub Issues](https://github.com/X1pheR/firefly-iii-mcp/issues) for bug reports and feature requests and pull requests for proposed changes. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the development workflow, test requirements and coding conventions. Security issues must follow the private process in [`SECURITY.md`](SECURITY.md).

Release changes are recorded in [`CHANGELOG.md`](CHANGELOG.md).

## Why another Firefly III MCP?

Reuse was the first choice. Hypershell reviewed multiple existing Firefly III MCP servers before building this adapter, and some candidates already offered tool filtering or a read-only mode. The decision to build was therefore **not simply that existing servers could write**.

The mismatch was broader: most existing projects are general-purpose Firefly III integrations that expose a large, API-shaped capability surface, while this project needed a small agent-facing financial-analysis interface. The required combination was:

- **semantic tools** for common financial questions instead of one MCP tool per API operation;
- **small tool context** so MCP clients do not carry a large Firefly schema catalog when only a focused read surface is needed;
- **data minimization** through bounded pagination/date ranges and deliberately reduced response objects;
- **hard read-only enforcement** at HTTP method and endpoint level, because the Firefly PAT itself has broad user authority;
- **no generic API escape hatch**, hidden mutation path, export/import surface or action-style rule execution;
- **a small trusted computing base** that is practical to audit, test and keep compatible with the Firefly version actually deployed;
- a simple **stdio deployment model** without requiring a separate network service.

[`daften/fireflyiii-mcp`](https://github.com/daften/fireflyiii-mcp) was the strongest reuse candidate and already had a read-only mode. At the reviewed revision, however, that mode filtered the published tool set by tool naming while the underlying implementation still contained a much broader generated API surface and mutation-capable client. Making it match the requirements above would have meant removing most of the tool catalog, replacing the safety model, adding response minimization and bounds, and then building the semantic analysis tools anyway. Carrying that delta as a fork would have been more code and more upstream-merge risk than maintaining this deliberately small adapter.

Other reviewed servers had similar product-fit gaps: broad CRUD/full-API coverage, capability groups that mixed reads and writes, generic execute/operation meta-tools, or filtering mechanisms that were not the hard method-and-endpoint boundary required here. Those can be valid designs for users who want broad Firefly control; they target a different use case.

The detailed review, including the read-only-mode analysis, reviewed upstream revisions and the reasons each primary candidate was not selected, is in [`docs/alternatives.md`](docs/alternatives.md).

This is a build-vs-reuse decision based on the combined agent UX, data-exposure, security and maintenance model—not a claim that community Firefly III MCP projects are defective.

## Status and compatibility

- Release line: `0.2.x`.
- Tested against Firefly III `6.6.6`.
- Firefly III source revision reviewed: `a95b82b14cb01b6e40491f2a94c53b47b71766e7`.
- Firefly III API docs revision reviewed: `fe6e96739ea9056c09d45e4fce1d471af23a2891` on branch `v6.6.6`.
- Requires Python `3.12` through `3.14`.
- MCP runtime: FastMCP `3.4.7`, stdio transport.

Later Firefly III versions may remain compatible, but they are not claimed as tested until their API contracts have been reviewed.

## Capability boundary

The v0.2 server exposes exactly **22 read-only tools** covering:

- application/API identity;
- accounts and balances;
- bounded transaction listing, detail and search;
- budgets and budget status;
- bills;
- categories and tags;
- piggy banks and recurrences;
- currencies and exchange rates;
- rule-group and rule inspection without execution;
- cashflow, spending-by-category and monthly summaries.

It intentionally excludes:

- generic HTTP/API passthrough;
- all create/update/delete endpoints;
- rule testing or execution;
- attachments and exports;
- imports, destructive data operations and purge actions;
- webhooks, cron and automation triggers;
- user/preferences/system administration;
- credential administration.

See [`docs/tools.md`](docs/tools.md) for the complete tool surface, bounds and output contract.

## Security model

Firefly III `6.6.6` Personal Access Tokens do **not** provide a useful read-only scope boundary. A dedicated MCP PAT therefore retains the authority of its Firefly III user. The MCP server is the primary technical read-only enforcement boundary.

The implementation adds the following controls:

1. Exactly 22 explicit semantic MCP tools are registered.
2. The HTTP client uses a fixed 25-endpoint allowlist.
3. Any HTTP method other than `GET` is rejected before network I/O.
4. No tool accepts an arbitrary HTTP method or path.
5. List pagination is bounded to at most 50 records per page.
6. Transaction/date-oriented reads default to 30 days and reject ranges over 366 days.
7. Notes are excluded unless a supported detail tool explicitly opts in.
8. Decimal JSON numbers are parsed with `Decimal` and returned as strings.
9. API errors are sanitized and never include bearer tokens, response bodies or query contents.
10. The PAT is loaded only from `FIREFLY_TOKEN_FILE`; it is never an MCP argument.
11. All MCP tools advertise `readOnlyHint=true`, `destructiveHint=false` and `idempotentHint=true`.

See [`SECURITY.md`](SECURITY.md) for vulnerability reporting and credential-handling guidance and [`docs/SECURE-DEVELOPMENT.md`](docs/SECURE-DEVELOPMENT.md) for the project security model.

## Installation and local use

The project is distributed as source and as a wheel attached to each GitHub Release. It is not currently published to PyPI.

For a local checkout:

```bash
git clone https://github.com/X1pheR/firefly-iii-mcp.git
cd firefly-iii-mcp
uv sync --frozen --all-groups
```

Create a private token file for a dedicated Firefly III Personal Access Token:

```bash
install -m 600 /dev/null ~/.config/firefly-iii-mcp.token
```

Write the PAT into that file using a local editor or another secret-safe mechanism. Do not place the real token in shell history, command-line arguments, tracked files or documentation.

A local MCP client can then start the stdio server with the installed entrypoint:

```json
{
  "command": "/absolute/path/to/firefly-iii-mcp/.venv/bin/firefly-iii-mcp",
  "args": [],
  "env": {
    "FIREFLY_BASE_URL": "https://firefly.example.com/api/v1",
    "FIREFLY_TOKEN_FILE": "/absolute/path/to/private/firefly-iii-pat"
  }
}
```

Both environment variables are required. `FIREFLY_BASE_URL` must point to the Firefly III `/api/v1` base URL. `FIREFLY_TOKEN_FILE` must be an absolute private regular file and must not be group/world accessible. Never put the PAT in command-line arguments, tracked configuration, logs or MCP responses.

## Development and verification

`uv.lock` is the canonical exact dependency resolution used by local verification and CI.

```bash
./scripts/verify.sh
```

The repository-owned verifier creates a fresh Python environment (3.12 by default, overridable with `VERIFY_PYTHON`), syncs the frozen lock, verifies the installed package version, compiles source/tests, runs Ruff, runs the full test suite with at least 90% coverage, and builds wheel/source artifacts. Hosted CI runs this verifier across Python 3.12, 3.13 and 3.14.

The tests include safe negative checks for the read-only boundary and synthetic API fixtures. They never need a real Firefly III PAT.

## Releases

Versions follow Semantic Versioning. Release tags are never reused. Public releases are built from an exact accepted tag and include a wheel, SHA-256 checksum and GitHub/Sigstore build-provenance attestation where supported.

See [`CHANGELOG.md`](CHANGELOG.md) for user-visible release notes.

## Upstream and license

Firefly III is a separate upstream project governed by its own license and project policies. This repository contains only the independent MCP integration maintained by Hypershell.

`firefly-iii-mcp` is licensed under the [MIT License](LICENSE).
