# Build vs. reuse review

This document records why Hypershell built `firefly-iii-mcp` instead of adopting or forking an existing Firefly III MCP implementation.

It is a decision record, not an evergreen ranking of community projects. Upstream projects may change after the review date.

- Review date: 2026-08-30
- Firefly III target: `6.6.6`
- Decision: build a small, semantic, bounded read adapter after reuse-before-build review

## What Hypershell needed

The requirement was not merely "an MCP that cannot create transactions." The target design combined several constraints that matter specifically for agent use over personal financial data:

1. **Semantic agent tools** — expose operations that match useful financial questions, such as monthly summary, cashflow and spending by category, rather than mirroring every Firefly III REST operation as a separate MCP tool.
2. **Small tool context** — keep the Firefly catalog compact enough that ChatGPT and Hermes can discover and select tools reliably without carrying a large API-shaped schema set in routine context.
3. **Data minimization** — bound pagination and date ranges, omit unnecessary fields, and avoid exports/attachments so a read-only call cannot still expose an unnecessarily large financial dataset.
4. **Hard read-only enforcement** — reject non-`GET` methods before network I/O and permit only an explicit endpoint allowlist. Firefly III Personal Access Tokens themselves do not provide a useful read-only authorization scope for this use case.
5. **No generic escape hatch** — no arbitrary path/method tool, generic execute operation, raw API proxy, hidden mutation dispatch, rule execution, import/export or administration surface.
6. **Small trusted computing base** — keep the amount of code that can handle a broad Firefly credential and financial data small enough to audit, test and version against the deployed Firefly release.
7. **Simple MCPJungle deployment** — run as a local stdio child without another independently exposed HTTP service or additional consumer credentials.

A project could therefore have a `read-only` option and still be a poor fit if it retained a very large API-shaped tool catalog, a mutation-capable client behind filters, unbounded/raw responses, or an architecture that would require a substantial long-lived fork.

## Primary candidates

Revision identifiers below are abbreviated snapshots of the source reviewed on 2026-08-30. They are included so the original decision can be reconstructed even if upstream projects later change.

| Project | Reviewed revision | Strengths | Why it was not selected unchanged |
| --- | --- | --- | --- |
| [`daften/fireflyiii-mcp`](https://github.com/daften/fireflyiii-mcp) | `852ca806` | Strongest reuse candidate; actively maintained; MIT; tests/CI; stdio and remote deployment options; broad Firefly coverage; tool filtering; explicit read-only mode. | The reviewed read-only mode classified tools by naming convention rather than enforcing a method-and-endpoint allowlist. The client still contained mutation methods and the project intentionally exposed a large generated API-shaped catalog. Matching Hypershell would still require removing most tools, replacing the safety boundary, adding bounded/minimized responses and adding semantic aggregate tools. |
| [`etnperlong/firefly-iii-mcp`](https://github.com/etnperlong/firefly-iii-mcp) | `1f14d7d3` | Mature TypeScript implementation with generated tools, presets/tags and a sizeable user base. | In the reviewed revision, visible-tool filtering and call dispatch did not use the same filtered registry: `tools/list` could hide tools while dispatch still searched the full generated tool set. For this threat model, hiding a tool was therefore not equivalent to making the capability unreachable. It also remained a broad API-shaped surface. |
| [`fabianonetto/mcp-server-firefly-iii`](https://github.com/fabianonetto/mcp-server-firefly-iii) | `6de6795a` | Well documented, tested and easy to consume; explicit tools; multiple transports; useful broad Firefly coverage. | Designed as a universal Firefly MCP with full CRUD and automation/export capabilities. Adopting it would require a substantial permanent reduction of both tool and implementation surface, plus new semantic/bounded response behavior. |
| [`horsfallnathan/firefly-iii-mcp-server`](https://github.com/horsfallnathan/firefly-iii-mcp-server) | `34ca8510` | Python implementation, validation/tests and flexible entity selection; supports both consolidated and direct modes. | The default consolidated design exposes a generic `firefly_execute(entity, operation, params)` capability and entity handlers include create/update/delete operations. Direct mode also exposes broad CRUD. A small visible tool count therefore does not imply a small capability surface. |
| [`vedantjain8/firefly-iii-mcp`](https://github.com/vedantjain8/firefly-iii-mcp) | `1fb39041` | Broad API coverage, stdio/HTTP support and startup group filtering; explicitly aims to provide read/write controls. | At the reviewed revision, `ENABLED_GROUPS` selected API groups rather than separating read operations from writes inside those groups. Groups such as accounts contained list/get together with create/update/delete. Its full-API objective and very large catalog were also the opposite of the intended semantic surface. |

## Why `daften/fireflyiii-mcp` read-only mode was not enough

`daften/fireflyiii-mcp` was the closest match and was the project most likely to be reused. Rejecting it was not based on the claim that it had no read-only support—it did.

At the reviewed revision, however, its read-only behavior was implemented by selecting tools whose names matched read-oriented prefixes such as `get_`, `search_` and `test_`. That is useful product-level filtering, but it is different from the boundary Hypershell required:

- the underlying Firefly client still implemented mutating HTTP methods;
- the server still carried the much larger generated full-API implementation;
- tool classification depended on naming rather than a fixed HTTP method and endpoint policy;
- action-like rule test operations remained part of the read-classified surface because they were `GET`/`test_` operations, while Hypershell intentionally excludes rule execution/testing from the finance read interface;
- the server returned API-oriented data rather than enforcing the same response minimization and financial-data bounds required here;
- its broad catalog remained unnecessary tool context even if only read operations were enabled.

None of those points makes the upstream design defective. They show that its `--read-only` goal and Hypershell's goal are different. The upstream mode answers "which of this large Firefly capability set should be exposed?"; Hypershell wanted "what is the smallest useful financial-analysis capability we should implement at all?"

## Other projects reviewed

These projects were also inspected during the reuse pass. They were not closer to the target than the primary candidates above.

| Project | Reviewed revision | Main mismatch |
| --- | --- | --- |
| [`Armgd/firefly-iii-mcp`](https://github.com/Armgd/firefly-iii-mcp) | `934e1b51` | Very broad FastMCP/API coverage with mutation operations; no equivalent hard bounded read profile found in the reviewed source. |
| [`OriginalByteMe/claude-open-finance`](https://github.com/OriginalByteMe/claude-open-finance) | `247213b9` | Workflow/plugin-oriented scope including imports, AI categorization and automation rules; substantially different product purpose. |
| [`kuuhakuDev/firefly-iii-mcp`](https://github.com/kuuhakuDev/firefly-iii-mcp) | `78438fab` | Hardened Go/runtime choices but broad read/manage operations including writes; no reviewed configuration that reduced the implementation to the required hard semantic read boundary. |
| [`milojarow/mcp-firefly`](https://github.com/milojarow/mcp-firefly) | `b4192301` | Full/near-full API coverage and a very large tool catalog; optimized for completeness rather than context economy and data minimization. |
| [`RadCod3/LamPyrid`](https://github.com/RadCod3/LamPyrid) | `66c88c9a` | Smaller apparent tool count, but included CRUD/create capabilities; tool count alone did not create the required capability boundary. |
| [`Knuckles-Team/firefly-iii-mcp`](https://github.com/Knuckles-Team/firefly-iii-mcp) | `85b3c56a` | Broad action-routed functionality including writes. The reviewed `--read-only` wording referred to container/root-filesystem hardening rather than making the Firefly API surface read-only. |

The review also searched for additional Firefly III MCP implementations beyond this table. No candidate found during that pass satisfied the full combination of semantic fit, hard read boundary, data minimization, small context surface and low adaptation cost.

## Why not fork a broader server?

Forking the strongest candidate would only have been worthwhile if the retained upstream implementation materially reduced our maintenance burden. In practice the required fork would have needed to:

1. remove or permanently suppress most generated API tools;
2. remove mutation paths rather than only hide their tool registrations;
3. replace name/group-based read filtering with explicit method and endpoint enforcement;
4. exclude action-like `GET` endpoints that do not belong in the finance-analysis surface;
5. introduce response minimization, pagination limits and date-range limits;
6. add the semantic aggregate tools that were the main agent-facing value;
7. adapt credential delivery and stdio runtime behavior to the existing MCPJungle deployment;
8. re-evaluate every upstream merge for newly added tools, endpoints or dispatch paths that could cross the boundary.

At that point Hypershell would own a large and security-sensitive delta against a codebase optimized for a different goal. The purpose-built adapter was smaller to implement, smaller to review and easier to keep reproducible against the deployed Firefly version.

## Decision summary

The decision was therefore **not**:

> Existing Firefly III MCP projects can write, so build a read-only one.

It was:

> Existing projects primarily optimize for broad Firefly API access. Hypershell needs a compact semantic financial-analysis interface with bounded data exposure, small model context, a hard method/endpoint read boundary and a small auditable implementation. Adapting the closest existing project to that shape would create a larger sustained fork than building the narrow adapter directly.

Read-only enforcement is one critical part of that decision, but not the sole reason.

## When reuse should be reconsidered

This is not a permanent NIH decision. Reuse or migration should be reconsidered if an upstream project evolves to provide most of the following without a large private patch set:

- a small semantic finance profile rather than only full-API tool generation;
- hard non-mutation enforcement independent of tool naming;
- explicit endpoint allowlisting or an equivalently auditable capability boundary;
- bounded/minimized financial responses;
- no generic operation/path escape hatch in the selected profile;
- a compact tool catalog suitable for agent context;
- stable tests and release/version compatibility evidence;
- a straightforward stdio deployment that does not require an additional service or credential boundary.

If that happens, replacing this adapter with a maintained upstream implementation would again be preferable to carrying unnecessary custom software.
