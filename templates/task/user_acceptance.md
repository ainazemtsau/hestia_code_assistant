# Чеклист ручной проверки — <module> — <T-id> — <title>

## Что проверяем вручную

<acceptance_block>

## Результат ручной проверки

- Статус: `pass` | `fail`
- Что выполнялось: (кратко перечислите)
- Что не выполнялось: (кратко перечислите)

## Оформление для `record-user-check`

- Отметьте все выполненные кейсы и приложите подтверждение (`evidence`), затем выполните:

```bash
python tools/csk/csk.py record-user-check <module-or-task> --result pass --notes "..." --checks "..." --evidence "..."
```

