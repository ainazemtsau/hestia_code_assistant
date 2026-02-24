# AGENTS (root)

Правила работы в этом репозитории (CSK‑Next):

1) Всегда начинай с `csk status --json`, затем действуй по `NEXT`.
2) Не запускай execution до прохождения Plan Gate (critic → freeze → approve).
3) Любая девиация процесса = incident (через `csk incident add` или автоматикой gate).
4) Не меняй файлы вне `allowed_paths` активного slice.
5) Любая команда должна завершаться `NEXT:` (если ты пишешь ответы пользователю).
6) Предпочитай маленькие слайсы и milestone‑1, остальное — placeholders.

