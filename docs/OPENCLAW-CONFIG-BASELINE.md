# OpenClaw Configuration Baseline (Security + Memory)

> This is an implementation baseline for OpenClaw deployments used with this project.

## 1) Gateway hardening
- Bind to loopback or private interface only.
- Use strong auth (token/password or trusted-proxy with strict allowlist).
- Never expose Gateway directly to public internet.

## 2) Trusted proxy (if used)
- Require `gateway.trustedProxies` explicit IP allowlist.
- Set `gateway.auth.mode = "trusted-proxy"`.
- Enforce identity header + required forwarded headers.

## 3) Memory governance
- Keep daily logs in `memory/YYYY-MM-DD.md`.
- Keep curated memory in `MEMORY.md`.
- Use retrieval-before-answer policy for history/preference questions.

## 4) PII policy
- Apply pre-LLM redaction and fail-close on redaction failures.
- Keep mapping store encrypted with strict ACL.
- Never persist raw secrets/PII in memory files.

## 5) Example config snippet (json5)
```json5
{
  gateway: {
    bind: "loopback",
    trustedProxies: ["127.0.0.1", "::1"],
    auth: {
      mode: "token"
    }
  },
  agents: {
    defaults: {
      compaction: {
        memoryFlush: {
          enabled: true,
          softThresholdTokens: 4000
        }
      }
    }
  }
}
```

## 6) Ops checklist
- [ ] Gateway not publicly reachable
- [ ] Auth mode enabled and tested
- [ ] Memory files present and writable
- [ ] PII redaction path tested with adversarial input
- [ ] Incident runbook reviewed monthly
