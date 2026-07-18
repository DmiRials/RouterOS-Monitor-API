# 📡 Router Monitor API

API для приема событий мониторинга и отправки уведомлений в Telegram через бота. 🚀

Проект рассчитан на сценарии вроде MikroTik Netwatch, Scheduler, DHCP/PPP scripts и других источников, которые умеют отправлять HTTP POST с JSON.

## ✨ Что умеет

- 📥 Принимает события через `POST /status`.
- 🔐 Проверяет API-токен из файла `tokens.conf`.
- 📬 Отправляет уведомления в Telegram через Bot API.
- ⚙️ Использует асинхронную очередь и отдельный Telegram worker.
- 📦 Ограничивает размер очереди, чтобы не раздувать память при потоке событий.
- 🔁 Повторяет отправку при временных ошибках Telegram, `429` и `5xx`.
- 🛡️ Не логирует секретные токены.
- 🧼 Экранирует пользовательский текст перед отправкой в Telegram HTML mode.
- 🔕 Пропускает повторные одинаковые статусы, чтобы не спамить одинаковыми UP/DOWN событиями.
- 🧾 Пишет логи в консоль и файл `logs/api.log` с ротацией.

## 🔄 Схема работы

```text
Источник события
      |
      | HTTP POST /status JSON
      v
Router Monitor API
      |
      | проверка token
      v
валидация payload
      |
      | дедупликация одинаковых status-событий
      v
очередь Telegram
      |
      v
Telegram Worker
      |
      | Telegram Bot API
      v
Telegram чат
```

## 📁 Структура проекта

```text
.
├── app/
│   ├── auth.py        # загрузка и проверка API-токенов
│   ├── cache.py       # кэш последних статусов для дедупликации
│   ├── config.py      # настройки из .env
│   ├── formatter.py   # форматирование Telegram-сообщений
│   ├── logger.py      # логирование
│   ├── main.py        # FastAPI app и lifecycle
│   ├── models.py      # Pydantic-модели входных данных
│   ├── queue.py       # очередь Telegram-задач
│   ├── routes.py      # HTTP endpoints
│   └── worker.py      # Telegram worker
├── logs/
├── requirements.txt
├── run.py
└── tokens.conf
```

## 🛠️ Установка

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## ⚙️ Настройка `.env`

Создай или обнови файл `.env` в корне проекта:

```env
BOT_TOKEN=123456789:telegram_bot_token
CHAT_ID=123456789

HOST=0.0.0.0
PORT=8000

TOKENS_FILE=tokens.conf

TELEGRAM_TIMEOUT=15
TELEGRAM_SILENT=false
TELEGRAM_MAX_RETRIES=3

QUEUE_MAX_SIZE=1000
MESSAGE_MAX_LENGTH=3900

LOG_DIR=logs
LOG_LEVEL=INFO

TELEGRAM_PROXY_ENABLED=false
TELEGRAM_PROXY_TYPE=socks5
TELEGRAM_PROXY_HOST=
TELEGRAM_PROXY_PORT=1080
TELEGRAM_PROXY_USER=
TELEGRAM_PROXY_PASSWORD=
```

Обязательные параметры:

- `BOT_TOKEN` - токен Telegram-бота.
- `CHAT_ID` - ID Telegram-чата.
- `TOKENS_FILE` - файл со списком разрешенных API-токенов.

Если `tokens.conf` отсутствует или в нем нет активных токенов, приложение не стартует.

## 🔑 Файл `tokens.conf`

Каждый разрешенный API-токен должен быть на отдельной строке:

```text
secret-token-1
secret-token-2
```

Пустые строки и строки с `#` игнорируются:

```text
# production
secret-token-1

# office routers
secret-token-2
```

Комментарии после токена тоже поддерживаются:

```text
secret-token-1 # main office
```

## ▶️ Запуск

```powershell
python run.py
```

По умолчанию API будет доступен на:

```text
http://127.0.0.1:8000/status
```

Если `HOST=0.0.0.0`, сервис слушает все сетевые интерфейсы.

## 🌐 API

### 📮 `POST /status`

Принимает JSON.

| Поле | Тип | Обязательно | Ограничение | Описание |
| --- | --- | --- | --- | --- |
| `token` | string | да | 1-256 | API-токен из `tokens.conf` |
| `company` | string | да | 1-128 | Компания или объект |
| `office` | string | нет | до 128 | Офис или площадка |
| `resource` | string | нет | до 128 | Ресурс, канал, устройство |
| `server` | string | нет | до 128 | Сервер или хост |
| `type` | string | нет | до 64 | Тип ресурса |
| `status` | boolean | условно | - | `true` = доступен, `false` = недоступен |
| `message` | string | условно | до 3900 | Произвольное сообщение |

Нужно передать либо `status`, либо `message`.

Если передан `message`, событие считается произвольным сообщением.
Если передан `status` без `message`, событие считается статусом мониторинга.

## 🧪 Примеры запросов

### 🚫 Проверка с неверным токеном

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/status" `
  -ContentType "application/json" `
  -Body '{
    "token": "wrong-token",
    "company": "Test Company",
    "status": false
  }'
```

Ожидаемый результат: HTTP `401`.

```json
{
  "detail": "Invalid token"
}
```

Токен в лог не записывается.

### 📶 Статус ресурса

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/status" `
  -ContentType "application/json" `
  -Body '{
    "token": "secret-token-1",
    "company": "Company",
    "office": "Main Office",
    "resource": "Internet",
    "server": "router-01",
    "type": "WAN",
    "status": false
  }'
```

Успешный ответ:

```json
{
  "accepted": true,
  "queued": true,
  "request_id": "A1B2C3D4"
}
```

### 🔁 Повторный одинаковый статус

Если отправить тот же `company`, `office`, `resource`, `server`, `type` и тот же `status` повторно, сообщение не попадет в очередь Telegram:

```json
{
  "accepted": true,
  "queued": false,
  "duplicate": true,
  "request_id": "A1B2C3D4"
}
```

Если статус изменится, например с `false` на `true`, событие снова будет поставлено в очередь.

### 💬 Произвольное сообщение

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/status" `
  -ContentType "application/json" `
  -Body '{
    "token": "secret-token-1",
    "company": "Company",
    "office": "Main Office",
    "message": "Alarm button pressed"
  }'
```

Успешный ответ:

```json
{
  "accepted": true,
  "queued": true,
  "request_id": "A1B2C3D4"
}
```

Поля `company`, `office`, `resource`, `server`, `type` и `message` экранируются перед отправкой в Telegram.

## 📋 Ответы и ошибки

| Код | Когда возникает |
| --- | --- |
| `200` | Событие принято, поставлено в очередь или пропущено как дубль |
| `401` | Неверный API-токен |
| `422` | Некорректный JSON или не передан ни `status`, ни `message` |
| `503` | Очередь Telegram переполнена |

Важно: успешный ответ API означает, что событие принято API. Фактическая отправка в Telegram происходит асинхронно в worker.

## 📬 Очередь и Telegram worker

Очередь ограничена настройкой `QUEUE_MAX_SIZE`.

Если Telegram временно недоступен, worker повторяет отправку до `TELEGRAM_MAX_RETRIES` раз:

- при сетевой ошибке или timeout;
- при HTTP `429`, учитывая `retry_after`, если он есть в ответе Telegram;
- при HTTP `5xx`.

При других ошибках Telegram, например `400`, задача не повторяется, потому что это обычно ошибка payload, chat id или bot token.

## 🧾 Логи

Логи пишутся:

- в консоль;
- в файл `logs/api.log`.

Файл лога ротируется: максимум 10 файлов по 10 MB.

Основные события:

```text
AUTH
REQUEST
MESSAGE
CACHE
QUEUE
WORKER
TELEGRAM
DONE
```

При неверном токене в лог пишется только факт отказа и IP клиента. Сам токен не логируется.

## ✅ Быстрая проверка

1. Запусти API:

```powershell
python run.py
```

2. Отправь запрос с неверным токеном. Должен быть `401`.

3. Отправь запрос с токеном из `tokens.conf`. Должен быть ответ с `"accepted": true`.

4. Повтори тот же status-запрос. Должен быть ответ с `"queued": false` и `"duplicate": true`.

5. Проверь `logs/api.log`.

## 📦 Зависимости

```text
fastapi
uvicorn
httpx[socks]
python-dotenv
pydantic
pydantic-settings
```

## 🔒 Примечания по безопасности

- 🔐 Не публикуй `BOT_TOKEN`, `CHAT_ID`, `.env` и `tokens.conf`.
- 🌍 Для доступа из интернета лучше использовать HTTPS reverse proxy.
- 🔄 Токены из `tokens.conf` применяются при старте приложения. После изменения файла перезапусти API.
- 🙈 Документация FastAPI отключена: `/docs`, `/redoc` и `/openapi.json` недоступны.
