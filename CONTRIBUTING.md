# Contributing to Firefly III MCP

Contributions and issue reports are welcome through the GitHub repository.

## Before opening a change

- Use a GitHub issue for bugs, feature requests or design discussion when the change is not self-explanatory.
- Use the private vulnerability-reporting process in `SECURITY.md` for security issues. Do not open a public issue for an undisclosed vulnerability.
- Keep this project a narrow semantic Firefly III read adapter. Avoid generic API passthrough, broad generated tool catalogs or unrelated orchestration behavior.
- Preserve the fixed GET-only endpoint boundary, bounded financial-data exposure and file-backed credential model.

## Development workflow

Create a branch, make one logically bounded change, and open a pull request against `main`.

The supported development baseline is Python 3.12 through 3.14 with `uv`. Use Ruff-compatible formatting and typing conventions already present in the codebase. Prefer explicit validation and fail-closed behavior at MCP, HTTP, configuration and credential boundaries.

Every functional change must include or update automated tests where a regression test is practical. Security-sensitive boundary changes require explicit negative coverage; data-minimization changes should prove that excluded fields remain excluded.

Run the repository validation before opening a pull request:

```bash
./scripts/verify.sh
```

The verifier is the canonical acceptance entry point. It creates a clean Python 3.12 environment from `uv.lock`, verifies package-version parity, compiles sources/tests, runs Ruff, runs pytest with the maintained coverage floor and builds the wheel.

GitHub CI must pass before a pull request is merged. CodeQL, OpenSSF Scorecard, Dependabot, Secret Scanning, Push Protection, immutable releases and release provenance provide additional public-repository security and supply-chain controls.

## Firefly III compatibility

The tested baseline is Firefly III 6.6.6. Changes that rely on a different Firefly API contract must include source/API evidence and contract tests before compatibility claims are updated.

Do not weaken the GET-only method check, fixed endpoint allowlist or response projection merely to make a new Firefly endpoint easier to expose. New tools should be justified as semantic agent workflows, not added only because an upstream endpoint exists.

## Dependencies

Direct dependencies and the lock file are maintained with Dependabot. Review new dependencies for necessity, maintenance, license, security history and transitive cost before adding them. GitHub Actions must remain pinned to full commit SHAs.

## Documentation

Update `docs/tools.md` whenever the public MCP tool contract changes. Update `README.md`, `SECURITY.md` or `docs/SECURE-DEVELOPMENT.md` when a change affects installation, compatibility, credentials, data exposure or trust boundaries.

User-visible release changes belong in `CHANGELOG.md`.

## Releases

Releases use strict SemVer tags. Release tags are never reused. The release workflow verifies source/tag/package-version parity, reruns the canonical verifier, checks reproducible package builds, publishes checksums and provenance, and only then publishes the GitHub Release.

## License

By contributing, you agree that your contribution is licensed under the repository's MIT license.
