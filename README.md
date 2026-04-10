<div align="center">

# BeamNG Skin Helper Bot

**Telegram-бот для создания скинов BeamNG.drive**

[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-26A5E4.svg?logo=telegram)](https://t.me/BeamNGSkinHelperBot)
[![BeamNG.drive](https://img.shields.io/badge/BeamNG.drive-FF6600.svg)](https://www.beamng.com/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![Deploy](https://github.com/fylhtq7779/HelperBotV2/actions/workflows/deploy.yml/badge.svg)](https://github.com/fylhtq7779/HelperBotV2/actions/workflows/deploy.yml)

*Отправь DDS-текстуру, выбери машину - получи готовый мод для установки в игру.*

</div>

---

## Что делает бот

Бот упрощает создание скинов для BeamNG.drive. Вместо того чтобы вручную собирать структуру мода (jbeam, materials.json, правильные пути), достаточно:

1. Отправить DDS-файл текстуры (2048x2048)
2. Ввести название скина
3. Выбрать машину из списка

Бот автоматически создаст ZIP-архив с правильной структурой, готовый к установке в игру.

## Поддерживаемые машины

40+ машин из стандартного набора BeamNG.drive: Autobello Piccolina, Bruckell Bastion, Gavril Barstow, Ibishu 200BX, Hirochi SBR4, Civetta Bolide и другие. Список обновляется автоматически при выходе новых версий игры.

## Как устроено

```
Пользователь          Telegram Bot           BeamNG.drive
    │                      │                      │
    ├── DDS-файл ─────────>│                      │
    ├── Название ─────────>│                      │
    ├── Выбор машины ─────>│                      │
    │                      ├── Генерация jbeam     │
    │                      ├── Генерация materials │
    │                      ├── Сборка ZIP ────────>│
    │<── Готовый мод ──────┤                      │
```

## Автообновление шаблонов

Шаблоны скинов берутся из мода [Skin Helper](https://www.beamng.com/resources/skin-helper.15037/). GitHub Actions ежедневно проверяет обновления мода и автоматически синхронизирует шаблоны - бот всегда совместим с последней версией игры.

## Стек

- **Python 3.12** + [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- **GitHub Actions** - автодеплой при push, ежедневная проверка обновлений шаблонов
- **systemd** - управление процессом на сервере

## Благодарности

Этот проект основан на моде **[Skin Helper](https://www.beamng.com/resources/skin-helper.15037/)** для BeamNG.drive.

Огромная благодарность автору мода **Beamer XD** за создание Skin Helper и шаблонов для всех машин, а также **@Top Tier Studios** за поддержку и развитие мода. Без их работы этот бот не имел бы смысла.

## Лицензия

MIT
</div>
