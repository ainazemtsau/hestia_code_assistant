# Phase 01 — CLI scaffold with mandatory NEXT block

## Objective
Собрать рабочий CLI `csk` со стабильной структурой вывода и подкомандами-заглушками. UX‑инвариант: каждая команда печатает `SUMMARY/STATUS/NEXT`.

## Deliverables
- CLI бинарь/entrypoint `csk`
- Подкоманды: `bootstrap`, `status`, `new`, `run`, `approve`, `module`, `validate`, `replay`
- Единый рендерер вывода (markdown/plain) с блоком `NEXT`.

## Tasks (atomic)
- [ ] Выбрать CLI фреймворк (Typer или argparse) и зафиксировать в ADR при необходимости.
- [ ] Реализовать `csk` без аргументов как alias для `csk status`.
- [ ] Реализовать шаблон вывода:
  - SUMMARY (список строк)
  - STATUS (таблица или список)
  - NEXT (recommended + optional OR)
- [ ] Добавить опцию `--json` для `csk status`.
- [ ] Все подкоманды пока могут печатать “NOT IMPLEMENTED”, но должны соблюдать формат и давать NEXT.

## Validation checklist
- [ ] `csk` печатает 3 секции и `NEXT:`
- [ ] `csk status --json` печатает валидный JSON
- [ ] Любая подкоманда печатает `NEXT` и exit code 0 (пока заглушки).


