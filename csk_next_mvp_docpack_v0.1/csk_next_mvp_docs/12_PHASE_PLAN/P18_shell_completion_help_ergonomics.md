# Phase 18 — Shell completion + help ergonomics

## Objective
Сделать CLI удобным: автодополнение для shell и хороший `--help`, чтобы пользователь не терялся.

## Deliverables
- `csk completion bash|zsh|fish` (или аналог)
- Док `examples/INSTALL_COMPLETION.md`

## Tasks (atomic)
- [ ] Реализовать генерацию completion (если Typer — встроенно; если argparse — вручную минимум).
- [ ] Добавить в help короткие примеры (“common flows”).
- [ ] Добавить `examples/INSTALL_COMPLETION.md` с инструкциями установки completion.

## Validation checklist
- [ ] `csk completion bash` печатает скрипт без ошибок
- [ ] `csk --help` показывает примеры и список основных команд


