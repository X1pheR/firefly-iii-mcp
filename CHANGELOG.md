# Changelog

All notable changes to Firefly III MCP are documented here. Versions follow Semantic Versioning.

## [0.2.0] - 2026-08-31

- Prepared the project for its first public release with public contribution, security, release and supply-chain documentation.
- Made `FIREFLY_BASE_URL` explicitly required instead of relying on a Hypershell-specific Docker hostname default.
- Added OpenSSF Scorecard workflow support, public-release provenance/checksum automation and public repository trust metadata.
- Expanded the build-vs-reuse documentation, including why existing read-only modes did not satisfy the complete semantic, bounded-data and auditability requirements.
- Kept the MCP capability contract at exactly 22 semantic read-only tools and the fixed 25-endpoint GET allowlist.

Security: this release removes an environment-specific implicit endpoint default and adds public supply-chain/security controls. No disclosed Firefly III MCP vulnerability was fixed in this release.

## [0.1.1] - 2026-08-30

- Fixed Firefly III 6.6.6 `/about` response handling against the observed flat `data` object contract.
- Added dependency-update policy and strengthened repository verification/documentation.

Security: no disclosed vulnerability was fixed in this release.

## [0.1.0] - 2026-08-30

- Initial private Hypershell release.
- Added the 22-tool semantic read-only Firefly III MCP surface, fixed GET-only endpoint allowlist, bounded financial responses, file-backed PAT handling, tests and release verification.

Security: no disclosed vulnerability was fixed in this release.
