#!/bin/bash
# Бэкап состояния бота: список пользователей и статистика скинов.
# Оба файла в .gitignore, в репозиторий не попадают - при переезде на другой
# сервер теряются вместе с ним, как уже случилось со старым сервером nl.
set -euo pipefail

SRC=/opt/skinbot/app
DST=/var/backups/skinbot
KEEP_DAYS=90

mkdir -p "$DST"
stamp=$(date +%F)
copied=0

for name in users.json skin_stats.json; do
    src="$SRC/$name"
    [ -s "$src" ] || continue

    base="${name%.json}"
    latest=$(ls -1t "$DST/$base-"*.json 2>/dev/null | head -1 || true)

    # не плодим одинаковые копии: если содержимое не менялось, пропускаем
    if [ -n "$latest" ] && cmp -s "$src" "$latest"; then
        continue
    fi

    cp "$src" "$DST/$base-$stamp.json"
    copied=$((copied + 1))
done

find "$DST" -name '*.json' -type f -mtime "+$KEEP_DAYS" -delete

if [ "$copied" -gt 0 ]; then
    logger -t skinbot-backup "сохранено файлов: $copied"
fi
