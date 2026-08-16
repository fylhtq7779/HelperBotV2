# Развёртывание

Файлы, которые лежат на сервере вне каталога бота.

## Что куда

```
skinbot.service          -> /etc/systemd/system/
skinbot-backup.service   -> /etc/systemd/system/
skinbot-backup.timer     -> /etc/systemd/system/
skinbot-backup.sh        -> /usr/local/bin/   (chmod +x)
```

После копирования:

```bash
systemctl daemon-reload
systemctl enable --now skinbot
systemctl enable --now skinbot-backup.timer
```

## Бот

Код в `/opt/skinbot/app`, виртуальное окружение в `/opt/skinbot/venv`.
Токен в `/opt/skinbot/app/.env` (`BOT_TOKEN=...`, права 600), в репозиторий не
попадает.

Сервер стоит в России, откуда Telegram недоступен, поэтому юнит поднимает весь
HTTP бота через локальный xray: `Environment=ALL_PROXY=socks5://127.0.0.1:10808`.
Код бота об этом не знает - python-telegram-bot читает прокси из окружения сам.
Если прокси не будет, бот упадёт с таймаутом на первом же запросе к API.

## Бэкап состояния

`users.json` и `skin_stats.json` перечислены в `.gitignore`, то есть в
репозитории их нет и при переезде на другой сервер они теряются - однажды так
и произошло вместе со списком пользователей.

Таймер раз в сутки копирует оба файла в `/var/backups/skinbot` с датой в имени,
хранит 90 дней и не плодит одинаковые копии. Бэкап локальный: от порчи файла
спасает, от потери самого сервера - нет.
