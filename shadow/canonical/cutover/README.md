# Canonical Cutover Workspace

This area owns the final replacement mechanics from canonical shadow into live:
- replace manifests
- delete manifests
- exact boundary mapping
- live mapping notes
- cutover checklist

The goal is a controlled cutover, not ad-hoc file movement.

Current canonical metadata:
- `boundary-map.json` — exact path-level ownership and cutover source of truth
- `live-replace-manifest.json` — exact live paths to replace from canonical
- `live-delete-manifest.json` — exact legacy paths to delete outright
