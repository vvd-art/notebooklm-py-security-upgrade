# Memory Governance

## Objective
Keep memory durable, useful, and safe. Reduce drift, contradictions, and privacy risk.

## 1) Memory Layers
- `memory/YYYY-MM-DD.md`
  - append-only daily operating log
  - raw context, work notes, temporary decisions
- `MEMORY.md`
  - curated long-term memory
  - stable preferences, durable decisions, recurring constraints

## 2) Write Criteria (Allowlist)
Write to `MEMORY.md` only if at least one applies:
1. recurring user preference
2. durable project decision/constraint
3. reusable operational rule
4. high-value lesson to prevent repeated failure

## 3) Do-Not-Store Rules
Never store:
- raw PII (phone/address/ID/account numbers)
- secrets/tokens/cookies
- unverified claims
- one-off noisy chatter

## 4) Retrieval Protocol
Before answering about prior work/decisions/dates/preferences/todos:
1. run semantic recall (memory search)
2. read only required snippets
3. answer with confidence level
4. state uncertainty if recall is weak

## 5) Maintenance Cadence
- Daily: append raw notes to daily file
- Weekly:
  - distill daily logs into `MEMORY.md`
  - remove duplicates/stale items
- Monthly:
  - prune outdated assumptions
  - compact and re-tag key themes

## 6) Privacy Classification
- P0 Public: can store as-is
- P1 Personal non-sensitive: minimal storage
- P2 Sensitive: store only redacted summary
- P3 Secret: never store in memory files

## 7) Quality Metrics
- contradiction count per week
- stale fact count
- retrieval hit rate on historical questions
- noise ratio in `MEMORY.md`
