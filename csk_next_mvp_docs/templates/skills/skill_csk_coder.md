# $csk-coder — Slice Execution Loop

## Purpose
Автономно прогонять slice loop (после того как изменения в коде уже сделаны) и продвигать статус.

## Inputs
- module_id, task_id
- slices.json
- worktree path

## Loop (per slice)
1) Определи следующий slice (не DONE).
2) Запусти:
   - `csk gate scope-check ...`
   - `csk gate verify ...`
3) Если оба PASSED:
   - write proof pack
   - mark slice DONE
4) Если FAIL:
   - зафиксируй incident (если ещё не зафиксирован)
   - остановись (не жги ретраи)
5) Всегда завершай `NEXT:`.

## Next rules
- Если blocked scope → NEXT: revert out-of-scope или revise plan (re-freeze)
- Если blocked verify → NEXT: fix tests/toolchain или update profile

