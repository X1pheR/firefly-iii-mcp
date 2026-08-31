# Secure development model

Firefly III MCP is a narrow semantic adapter around Firefly III. Its security model assumes that the stdio process is launched only by a trusted MCP client or gateway and that the Firefly III Personal Access Token is a broad credential whose mutation authority must be constrained by this adapter.

## Trust and privilege boundaries

- Firefly III remains the data and identity system. Its Personal Access Token is not treated as a read-only authorization primitive.
- The MCP server exposes exactly 22 named semantic read tools and no generic HTTP, arbitrary endpoint or action executor.
- The internal HTTP client rejects every method except `GET` before network I/O and accepts only a fixed reviewed endpoint enum.
- Financial response data is projected into purpose-specific model-visible structures with bounded pagination/date windows and opt-in notes.
- Credentials are file-backed. The PAT is not accepted as an MCP argument or command-line argument.
- Public GitHub workflows use synthetic fixtures and do not receive Firefly or production Homelab credentials.

## Secure design principles

The project applies the following principles during changes and review:

- **Economy of mechanism:** keep the adapter small, semantic and purpose-specific instead of projecting the complete Firefly API into MCP.
- **Fail-safe defaults:** missing required configuration, unsafe credential permissions, unknown endpoints, unsupported methods and out-of-bounds requests fail closed.
- **Complete mediation:** method and endpoint checks occur on each internal request rather than depending on which MCP tool called the client.
- **Open design:** security does not depend on source secrecy. Tool contracts, exclusions, tests and the endpoint/method enforcement model are documented.
- **Least privilege:** the process receives only a Firefly endpoint and file-backed credential, while the MCP surface exposes only the read workflows required by the product.
- **Least common mechanism:** no shared generic request tool, arbitrary URL input or mutation-capable compatibility layer is exposed.
- **Limited attack surface:** 22 fixed MCP tools map to 25 fixed GET endpoint templates rather than a generated full-API catalog.
- **Allowlist-oriented validation:** HTTP methods, endpoints, path parameters, pagination, date ranges and credential-file permissions are constrained explicitly.
- **Data minimization:** tool outputs omit unnecessary upstream fields and limit the amount of financial history retrievable per request.
- **Least astonishment:** every tool is annotated read-only, non-destructive and idempotent and the documentation states the important exclusions.

## Common vulnerability classes and mitigations

| Risk | Current mitigation |
| --- | --- |
| Broken authorization / excessive capability | The Firefly PAT is assumed broad; the MCP implements a fixed read-only method/endpoint boundary and no generic request tool. |
| SSRF / arbitrary HTTP access | Callers cannot supply a request URL or path. `FIREFLY_BASE_URL` is operator configuration and tool calls select only predefined endpoint templates. |
| Credential exposure | PAT input is restricted to a private regular file; API errors are sanitized; public tests use synthetic credentials only. |
| Sensitive financial-data exposure | Pagination and date windows are bounded; responses are projected; notes are opt-in; exports and attachments are absent. |
| Injection through path values | Path parameters are inserted only into known templates and URL-quoted before I/O. |
| Malformed upstream data | JSON parsing failures become sanitized API errors; decimal values are normalized without leaking raw response bodies. |
| Dependency / supply-chain compromise | Exact application dependencies are locked, GitHub Actions are commit-pinned, Dependabot is configured, CodeQL and OpenSSF Scorecard are enabled for the public repository, and releases publish checksums plus GitHub/Sigstore provenance. |
| Policy regression | Unit and contract tests cover the exact tool inventory, write-tool absence, HTTP method rejection, endpoint allowlisting, credential permissions, data minimization and compatibility fixtures. |

## Security review expectations

Changes that affect MCP schemas, HTTP methods/endpoints, credential handling, financial response projection, date/pagination bounds, dependencies, release provenance or Firefly compatibility require explicit security review in addition to ordinary functional tests. A fixed boundary defect should receive a regression test before release.

Security vulnerabilities must follow [`SECURITY.md`](../SECURITY.md). Contribution and test requirements are defined in [`CONTRIBUTING.md`](../CONTRIBUTING.md).
