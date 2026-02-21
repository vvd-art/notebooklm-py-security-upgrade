# Changelog — Security & Memory Governance Upgrade

## Added
- `docs/SOUL-POLICY.md`
  - action tiers
  - confirmation matrix
  - group chat response policy
  - incident mode
- `docs/MEMORY-GOVERNANCE.md`
  - memory lifecycle and write criteria
  - retrieval protocol
  - privacy classification and maintenance cadence
- `docs/PII-GATEWAY-SPEC.md`
  - redaction/rehydration pipeline
  - fail-close controls
  - logging and incident response requirements

## Changed
- Standardized policy language for external actions and security-impacting operations.
- Established explicit "do-not-store" memory constraints for secrets and raw PII.

## Operational Impact
- Reduced accidental external actions.
- Improved memory quality and lower contradiction drift.
- Lower risk of sensitive data exposure in model/tool pipelines.
