# Phase 00 — Bootstrap skeleton and repo contract

## Objective
Сформировать минимальный файловый контракт `.csk/` + `.agents/skills/` + `AGENTS.md`, чтобы дальнейшие фазы могли добавлять функциональность без спорных “куда класть файлы”.

## Deliverables
- Директории: `.csk/engine/`, `.csk/local/`, `.csk/app/`, `.agents/skills/`
- Файлы-заглушки:
  - `.csk/engine/VERSION`
  - `.csk/local/config.json`
  - `.csk/app/registry.json` (может быть пустым)
  - `AGENTS.md` (root)
- Команда `csk bootstrap` (пока может просто создавать структуру).

## Tasks (atomic)
- [ ] Добавить в репозиторий структуру директорий согласно `03_DIRECTORY_LAYOUT.md`.
- [ ] Создать `VERSION` и записать текущую версию engine.
- [ ] Создать `local/config.json` (минимум: default_profile, allowlist/denylist команд).
- [ ] Создать пустой `registry.json` (валидный JSON).
- [ ] Создать `AGENTS.md` в root с 5–10 правилами для ассистентов (коротко, без “воды”).
- [ ] Добавить `.agents/skills/.gitkeep` (или аналог), чтобы директория существовала.

## Validation checklist
- [ ] `ls -la .csk` показывает engine/local/app
- [ ] `cat .csk/engine/VERSION` возвращает строку версии
- [ ] `python -m csk bootstrap` (или `csk bootstrap`) создаёт структуру повторно без ошибок (идемпотентность).


