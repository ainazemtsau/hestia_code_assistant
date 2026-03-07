---
name: pf-retro
description: Провести ретро: собрать проблемы, обновить KNOWLEDGE/PKM, обновить stale docs.
---

# Обязательные tool calls
1) `pf status --json`
2) `pf context build --intent retro`

# Процесс

1) Собери список проблем:
- из incidents (если есть)
- из провалов verify
- из замечаний review
- из фидбэка пользователя

2) Запиши retro файл:
- `.pf/modules/<module>/RETRO/<date>.md`

3) Обнови память:
- обнови `.pf/modules/<module>/KNOWLEDGE.md` (только проверенные команды)
- при необходимости добавь PKM items (`pf pkm upsert`)

4) Docs freshness:
- `pf docs check`
- если stale docs есть:
  - обнови docs
  - `pf docs mark-fixed --path ...`

5) Завершение:
- append event `retro.completed`

# Запреты
- не придумывай “универсальные” правила без связи с конкретным инцидентом
