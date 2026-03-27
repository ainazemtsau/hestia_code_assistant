# Canonical Delivery

This subtree will hold the thin install/update delivery layer for the canonical client package.

Stage ownership:
- `Stage 8`

Delivery comes after runtime and client-package design. It is not the architectural center of the product.

Canonical documents in this subtree:

- `DELIVERY_BOUNDARIES.md`
- `MANIFEST_CONTRACT.md`
- `APPLY_RULES.md`

These documents define:

- the Stage 8A thin-delivery boundary
- the Stage 8A ownership-aware manifest contract for install/update materialization
- the Stage 8B concrete install/update action matrix and runtime-generation handoff timing
