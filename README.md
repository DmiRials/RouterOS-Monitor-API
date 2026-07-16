# Router Monitor API

> Универсальный API для приема событий от MikroTik и отправки уведомлений в Telegram.

## Возможности

- 🚀 FastAPI
- 🔐 Авторизация по API Token
- 📨 Отправка уведомлений в Telegram
- 📬 Очередь сообщений (Telegram Worker)
- 🔄 Автоматический Retry при ошибках Telegram
- 🔕 Поддержка тихих уведомлений
- 🌐 HTTPS через Nginx
- 📄 Логирование всех запросов
- ⚡ Высокая скорость обработки запросов
- 📦 Сборка в единый бинарный файл

---

# Принцип работы

```text
                MikroTik
                    │
             HTTPS POST JSON
                    │
                    ▼
          Router Monitor API
                    │
          Проверка API Token
                    │
         Формирование сообщения
                    │
         Добавление в очередь
                    │
          Telegram Worker
                    │
             Telegram Bot API
                    │
                    ▼
                Telegram
```

---

# Возможности API

Поддерживаются два типа событий.

## 1. Мониторинг ресурсов

Используется для:

- Netwatch
- Проверки Интернета
- Проверки VPN
- Проверки серверов
- Проверки шлюзов

Пример уведомления

```
✅ Компания | Главный офис | Интернет | доступен
```

или

```
❌ Компания | Главный офис | Интернет | недоступен
```

---

## 2. Произвольные сообщения

Используется для:

- Тревожной кнопки
- SMS
- Уведомлений Scheduler
- Firewall событий
- DHCP событий
- Любых пользовательских сообщений

Пример

```
🚨 Компания | Главный офис

Тревожная кнопка сработала
```

---

# API

```
POST /status
```

### JSON параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| token | string | API Token |
| company | string | Компания |
| office | string | Офис |
| resource | string | Контролируемый ресурс |
| server | string | Сервер |
| type | string | Тип ресурса |
| status | bool | Состояние ресурса |
| message | string | Произвольное сообщение |

---

## Пример запроса (Netwatch)

```json
{
    "token": "TOKEN",
    "company": "Компания",
    "office": "Главный офис",
    "resource": "Интернет",
    "status": true
}
```

---

## Пример запроса (Произвольное сообщение)

```json
{
    "token": "TOKEN",
    "company": "Компания",
    "office": "Главный офис",
    "message": "🚨 Тревожная кнопка сработала"
}
```

---

# Ответ API

Успешная обработка

```json
{
    "success": true,
    "queued": true,
    "request_id": "A1B2C3D4"
}
```

---

# Конфигурация

Все параметры приложения находятся в файле

```
.env
```

Основные параметры

```
BOT_TOKEN=
CHAT_ID=

HOST=
PORT=

TOKENS_FILE=

TELEGRAM_TIMEOUT=
TELEGRAM_RETRIES=
TELEGRAM_SILENT=
```

---

# API Token

Авторизация производится по токену.

Все разрешенные токены находятся в файле

```
tokens.conf
```

Каждый токен должен располагаться на отдельной строке.

```
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy
```

---

# MikroTik

Для отправки событий используется единый скрипт

```
MyApiSend
```

Скрипт может использоваться из:

- Netwatch
- Scheduler
- DHCP Lease Script
- PPP Profile
- SMS Scripts
- Firewall
- Любого RouterOS Script

---

# Telegram

Для предотвращения ошибок Telegram 429 используется отдельный Worker.

Все сообщения:

- помещаются в очередь;
- отправляются последовательно;
- автоматически повторяются при ошибках.

Это позволяет одновременно принимать большое количество событий без потери сообщений.

---

# Логирование

Все действия записываются в лог.

Основные события

```
REQUEST
AUTH
MESSAGE
QUEUE
WORKER
TELEGRAM
DONE
```

---

# HTTPS

Для безопасной передачи данных рекомендуется использовать Reverse Proxy.

Рекомендуемая схема

```
Internet
      │
HTTPS
      │
Nginx
      │
HTTP
      │
Router Monitor API
```

---

# Запуск

Запуск приложения

```
./run
```

или через systemd

```
systemctl start router-monitor
```

Статус

```
systemctl status router-monitor
```

Логи

```
journalctl -u router-monitor -f
```

---

# Используемые технологии

- Python 3.13
- FastAPI
- Uvicorn
- HTTPX
- Pydantic
- Nginx
- Telegram Bot API
- RouterOS
- Systemd

---

# Лицензия

MIT License

---

# Автор

**DmiRials**

GitHub: https://github.com/DmiRials
