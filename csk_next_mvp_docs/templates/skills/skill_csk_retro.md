# $csk-retro — Retro Wizard

## Purpose
Собрать проблемы (incidents) и превратить их в улучшения Overlay.

## Inputs
- incidents.jsonl
- verify logs summary
- user notes (optional)

## Output
- retro.md with clusters + concrete proposals
- patch proposals in `.csk/local/`

## Must
- event `retro.completed`
- NEXT: `csk status`

