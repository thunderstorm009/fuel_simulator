# Risk register
| Risk | Impact | Mitigation | Trigger |
|---|---|---|---|
| Guide, live simulator and kit disagree | Wrong integration | Verify in Sprint 1; record in sim-findings.md | Live response differs |
| Time overrun | Core workflow incomplete | P0/P1/P2, cut P2 first, scope-cut prompt | Sprint gate missed |
| Agent rewrites earlier work or starts a new project | Regression, lost time | ONE REPOSITORY rule, PROGRESS.md, UNSTICK prompt, review | Large unexplained diff |
| Agent context lost or quota hit | Stalled work | RESUME prompt, switch tools, PROGRESS.md | Session reset |
| Stale or malformed data | Bad recommendation | Freshness flags, validation, block submit | Stale header |
| Duplicate or invalid submission | Unsafe action | Stored idempotency key, re-validation, human approval | Retry or double click |
| Weak forecast claims | Credibility loss | Baseline, disclose limits, measure error | Sparse history |
| Docker networking | App cannot reach simulator | Explicit env config, smoke test | Connection errors |
| Unverified demo claims | Credibility loss | Evidence folder, auditor | Missing output |
| Third-party skill risk | Unsafe commands | Use only the 12 kit skills; read any new skill first | New skill added |
