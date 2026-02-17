# Codex setup (CSK‑M Pro v2)

## Trust the project
Codex loads `.codex/config.toml` only for trusted projects.

## Rules (recommended)
Install conservative CSK rules:
```bash
python tools/csk/install_rules.py
```
Restart Codex after changes.

## MCP (optional)
Enable MCP only when it gives big ROI (UI/E2E, docs).
Add via CLI:
```bash
codex mcp add playwright -- npx -y @playwright/mcp
codex mcp list
```
