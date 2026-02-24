# 09 — Context Builder v1 (MVP)

## Цель v1
Собирать для ассистента **детерминированный Context Bundle**:
- компактный,
- с provenance,
- с базовой оценкой свежести,
- без тяжёлых индексов (vector/graph).

## Вход
- task_id / mission_id / module_id
- token_budget (или character budget)
- allowed_paths (из slices.json)
- event log (последние события по модулю/таску)

## Выход: Context Bundle (JSON + сохранение в файл)
Файл: `<module>/.csk/tasks/T-####/run/context/bundle-<id>.json`

Секции (MVP):
1) `task_brief` — цель, acceptance, scope/non-scope (из plan.md, slices.json)
2) `allowed_paths` — список путей и комментарии
3) `relevant_files` — top-N файлов по lexical сигналам внутри allowed_paths
4) `recent_evidence` — последние логи verify/ошибок (с event ids)
5) `runbook` — PKM items v0 (например “как запустить тесты”)

## Lexical retrieval (MVP алгоритм)
- извлечь ключевые слова:
  - из spec/plan (заголовки, bullet points),
  - из последних ошибок verify (stderr).
- candidate files = `git ls-files` внутри allowed_paths
- score = сумма:
  - совпадений ключевых слов в пути/имени файла,
  - совпадений в первых N строках файла,
  - бонус за “недавние изменения” (если файл был изменён в активном worktree)
- взять top-N (например 10)

## Provenance (обязательное)
Каждый item должен иметь `source`:
- file span: `(path, start_line, end_line)`
- или event reference: `event_id`

## Freshness report (MVP)
- `repo_head` (commit)
- `bundle_created_ts`
- `staleness_hint`:
  - если после создания bundle изменились файлы в allowed_paths → пометить “possibly stale”
  - иначе “fresh”

## Интеграция
Команда: `csk context build --task T-0001 --budget 3200`
Событие: `context.bundle.built` (с algo_version = `cb.v1`)

