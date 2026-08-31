## Summary

Describe the bounded change and why it belongs in Firefly III MCP.

## Verification

- [ ] `./scripts/verify.sh` passes.
- [ ] Functional changes add or update automated tests where practical.
- [ ] MCP/tool contract changes update `docs/tools.md`.
- [ ] User-visible changes update `CHANGELOG.md`.

## Security and data boundary

- [ ] No credential, real financial data or private infrastructure detail is included.
- [ ] The change preserves the fixed GET-only method/endpoint boundary.
- [ ] The change preserves bounded financial-data exposure and does not add a generic API escape hatch.
- [ ] Any changed trust boundary has explicit negative/regression coverage.
