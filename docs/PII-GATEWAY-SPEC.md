# PII Gateway Specification

## Objective
Prevent raw sensitive data from reaching model/tool chains by default.

## 1) Protected Data Classes
- email
- phone numbers
- physical addresses
- government IDs / account identifiers
- API keys, tokens, cookies, credentials
- personal names when policy requires masking

## 2) Processing Pipeline
1. **Pre-LLM Redaction**
   - detect PII in prompts/tool payloads
   - replace with deterministic placeholders (e.g., `<PII_EMAIL_01>`)
2. **Model/Tool Execution**
   - downstream receives tokenized placeholders only
3. **Post-LLM Rehydration**
   - re-map placeholders only for permitted user-visible outputs
4. **Audit Logging**
   - log rule hits and outcomes without raw PII

## 3) Security Controls
- fail-close: if redaction fails, block request
- encrypted mapping store at rest
- strict ACL with least privilege
- TTL + rotation for mapping entries
- key material separated from app runtime

## 4) Logging Policy
Log:
- timestamp
- actor/channel
- rule ID
- action outcome

Do NOT log:
- raw PII values
- full secret payloads

Optional:
- hashes/fingerprints for correlation

## 5) Incident Response
Trigger on:
- redaction bypass
- plaintext PII detected outbound
- anomalous mapping-store access

Response:
1. stop outbound path
2. rotate/revoke secrets and tokens
3. preserve forensic logs
4. notify owners
5. patch rule + add regression test

## 6) Test Requirements
- Unit:
  - detector coverage by data class
  - fail-close behavior
- Integration:
  - redaction/rehydration roundtrip
  - assert no plaintext PII in downstream payloads
- Adversarial:
  - obfuscated PII formats
  - prompt-injection attempts to force reveal
