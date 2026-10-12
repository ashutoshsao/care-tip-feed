# Reading the profile safely ⏱ 1.5 min

- Every fact = **code + status + verbatim quote** — "tests to be completed" ≠ "results received"
- Checks: code first (quote exists? words fit status?) → LLM only if flagged → unsure = safer status + clinician
- Haiku 5.5: **0/84** safety errors · GPT-6 Luna: 1 error, caught by the negation check · ~$0.0015 per profile

```json
{
  "red_flags": [{ "code": "suspected_cardiac", "status": "active",
                  "quote": "intermittent chest pain and left-hand numbness" }],
  "tests":     [{ "code": "thyroid_panel", "status": "scheduled",
                  "quote": "to be completed this week" }],
  "issues":    [{ "code": "menstrual_pain", "status": "confirmed",
                  "severity": "severe", "quote": "severe menstrual pain" }]
}
```

Code then checks it: is each quote really in her profile, and do the words fit the status?

> Say: "Errors will happen — the goal is rare, visible, and cheap."
