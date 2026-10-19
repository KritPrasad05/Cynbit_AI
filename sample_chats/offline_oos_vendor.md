# Sample chat — Out-of-scope vendor pitch (graceful redirect)

Source: **offline engine** run (deterministic, no network) on a novel synthetic input, 2026-10-19.

## Input

```text
We are a staffing agency placing offshore developers. Would you like to review our talent pool rates? We offer 20% first-order discount on all profiles.
```

## Output (LeadBrief, abridged)

- **Mode:** `offline_rules` · model: deterministic-rules (TF-IDF/LogReg + templates) · latency: 1 ms · tokens in/out: 0/0 · prompt vv3
- **Out of scope:** True — Matched out-of-scope pattern: vendor_pitch
- **Suggested response:** Thanks for reaching out. Cynbit is not evaluating new vendor partnerships through this channel; if that changes we will contact you.

## Annotation

OOS: detected by keyword rules, no services invented, polite redirect drafted. Note the vendor's own 'discount' phrasing does NOT trip the injection patterns (correct — it's a real offer, not an attack on our prompt).
