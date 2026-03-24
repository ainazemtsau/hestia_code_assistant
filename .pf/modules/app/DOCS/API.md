---
pf_doc:
  scope: module:app
  sources:
    - path: app/api.txt
      mode: file-sha
  freshness:
    policy: strict
    stale_on_any_change: true
---

# API
