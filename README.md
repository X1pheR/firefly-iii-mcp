# Firefly III MCP

`firefly-iii-mcp` is a Hypershell-maintained Model Context Protocol (MCP) server for strictly read-only, bounded access to [Firefly III](https://github.com/firefly-iii/firefly-iii). It is an independent integration and is not affiliated with, endorsed by, or maintained by the Firefly III project.

The server intentionally exposes a small semantic financial-analysis surface instead of generating or proxying the complete Firefly III API. This keeps mutations, automation and arbitrary HTTP access absent from the MCP contract.

## Why another Firefly III MCP?

Reuse was the first choice. Hypershell reviewed multiple existing Firefly III MCP servers before building this adapter, and some candidates already offered tool filtering or a read-only mode. The decision to build was therefore **not simply that existing servers could write**.

The mismatch was broader: most existing projects are general-purpose Firefly III integrations that expose a large, API-shaped capability surface, while Hypershell needed a small agent-facing financial-analysis interface. The required combination was:

- **semantic tools** for common financial questions instead of one MCP tool per API operation;
- **small tool context** so ChatGPT and Hermes do not carry a large Firefly schema catalog when only a focused read surface is needed;
- **data minimization** through bounded pagination/date ranges and deliberately reduced response objects;
- **hard read-only enforcement** at HTTP method and endpoint level, because the Firefly PAT itself has broad user authority;
- **no generic API escape hatch**, hidden mutation path, export/import surface or action-style rule execution;
- **a small trusted computing base** that is practical to audit, test and keep compatible with the Firefly version actually deployed;
- a simple **stdio deployment fit** for the existing MCPJungle runtime without adding another remote service layer.

[`daften/fireflyiii-mcp`](https://github.com/daften/fireflyiii-mcp) was the strongest reuse candidate and already had a read-only mode. At the reviewed revision, however, that mode filtered the published tool set by tool naming while the underlying implementation still contained a much broader generated API surface and mutation-capable client. Making it match the requirements above would have meant removing most of the tool catalog, replacing the safety model, adding response minimization and bounds, and then building the semantic analysis tools anyway. Carrying that delta as a fork would have been more code and more upstream-merge risk than maintaining this deliberately small adapter.

Other reviewed servers had similar product-fit gaps: broad CRUD/full-API coverage, capability groups that mixed reads and writes, generic execute/operation meta-tools, or filtering mechanisms that were not the hard method-and-endpoint boundary required here. Those can be valid designs for users who want broad Firefly control; they target a different use case.

The detailed review, including the read-only-mode analysis, reviewed upstream revisions and the reasons each primary candidate was not selected, is in [`docs/alternatives.md`](docs/alternatives.md).

This is a build-vs-reuse decision based on the combined agent UX, data-exposure, security and maintenance model—not a claim that community Firefly III MCP projects are defective.

## Status and compatibility

- Release line: `0.1.x`.
- Tested against Firefly III `6.6.6`.
- Firefly III source revision reviewed: `a95b82b14cb01b6e40491f2a94c53b47b71766e7`.
- Firefly III API docs revision reviewed: `fe6e96739ea9056c09d45e4fce1d471af23a2891` on branch `v6.6.6`.
- Requires Python `3.12` through `3.14`.
- MCP runtime: FastMCP `3.4.7`, stdio transport.

Later Firefly III versions may remain compatible, but they are not claimed as tested until their API contracts have been reviewed.

## Capability boundary

The v0.1 server exposes exactly **22 read-only tools** covering:

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

The production Hypershell deployment keeps Firefly tooling out of the routine `agent-fast` group to avoid adding financial tool schemas to the default tool context. It is exposed through `agent-admin` when needed. That group placement is a context/catalog optimization, not an authorization boundary; the Firefly MCP itself enforces the read-only capability boundary.

See [`SECURITY.md`](SECURITY.md) for vulnerability reporting and credential-handling guidance.

## Installation and local use

This repository is currently private and is not published to PyPI. Hypershell production consumes an exact tagged source revision and builds a versioned local runtime; the running MCP child does not receive GitHub credentials.

For an authorized local checkout:

```bash
uv sync --frozen --all-groups
```

A local MCP client can then start the stdio server with the installed entrypoint:

```json
{
  "command": "/absolute/path/to/firefly-iii-mcp/.venv/bin/firefly-iii-mcp",
  "args": [],
  "env": {
    "FIREFLY_BASE_URL": "https://firefly.example.com/api/v1",
    "FIREFLY_TOKEN_FILE": "/absolute/path/to/private/firefly-iii-pat",
    "FIREFLY_TIMEOUT_SECONDS": "15"
  }
}
```

`FIREFLY_BASE_URL` must point to the Firefly III `/api/v1` base URL. `FIREFLY_TOKEN_FILE` must be an absolute private regular file and must not be group/world accessible. Never commit the PAT, put it in command-line arguments, or expose it through logs or MCP responses.

## Development and verification

`uv.lock` is the canonical exact dependency resolution used by local verification and CI.

```bash
./scripts/verify.sh
```

The repository-owned verifier creates a fresh Python 3.12 environment, syncs the frozen lock, verifies the installed package version, compiles source/tests, runs Ruff, runs the full test suite with at least 90% coverage, and builds a wheel.

The tests include safe negative checks for the read-only boundary and synthetic API fixtures. They never need a real Firefly III PAT.

## Upstream and license

Firefly III is a separate upstream project governed by its own license and project policies. This repository contains only the independent MCP integration maintained by Hypershell.

`firefly-iii-mcp` is licensed under the [MIT License](LICENSE).
