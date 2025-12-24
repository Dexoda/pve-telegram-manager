# PVE Telegram Manager

Асинхронный Telegram-бот для полноценного управления гипервизором Proxmox VE 8.4.0.

## 🚀 Возможности

### Управление виртуальными машинами
- 📋 Просмотр списка всех VM/LXC контейнеров
- ▶️ Запуск, остановка, перезагрузка VM
- ℹ️ Детальная информация о VM (CPU, RAM, диски, сеть)
- ⭐ Избранные VM для быстрого доступа
- 🖥️ NoVNC доступ для удаленного управления

### Мониторинг системы
- 📊 Мониторинг ресурсов (CPU, RAM, Load Average)
- 🌡️ Температура процессора
- 💾 SMART статус дисков
- 📶 Статистика сети
- 💿 Использование дисков

### Управление хранилищем
- 📦 Список всех storage
- 💿 Управление ISO образами
- 📥 Скачивание ISO из интернета
- 💾 Управление бэкапами

### Системные инструменты
- 🔍 Ping хостов
- 🛣️ Traceroute
- 📝 Системные логи (journalctl)
- 📋 Логи Proxmox
- 🔄 Обновление системы

### Финансы
- 💰 Калькулятор стоимости электричества (прогрессивные тарифы Алматы 2025)
- 📊 Расчет по 3 ступеням: 0-150 кВт⋅ч, 150-300 кВт⋅ч, 300+ кВт⋅ч
- 💵 Команда `/cost` для быстрого расчета стоимости

### Безопасность
- 🔐 Авторизация по списку admin ID
- 📝 Логирование всех команд
- 🔔 Алерты при критических событиях

## 📋 Требования

- Python 3.11+
- Proxmox VE 8.4.0+
- Telegram Bot Token
- Proxmox API Token

## 🛠️ Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/Dexoda/pve-telegram-manager.git
cd pve-telegram-manager
```

### 2. Настройка окружения

Скопируйте `.env.example` в `.env` и заполните своими данными:

```bash
cp .env.example .env
nano .env
```

Обязательные переменные:
- `TELEGRAM_BOT_TOKEN` - токен бота от @BotFather
- `ADMIN_IDS` - список ID администраторов через запятую
- `PVE_HOST` - IP адрес Proxmox сервера
- `PVE_TOKEN_NAME` - имя API токена
- `PVE_TOKEN_VALUE` - значение API токена

Дополнительные переменные (опциональные):
- `TARIFF_STEP_1` - тариф 0-150 кВт⋅ч (по умолчанию: 23.21 KZT)
- `TARIFF_STEP_2` - тариф 150-300 кВт⋅ч (по умолчанию: 28.50 KZT)
- `TARIFF_STEP_3` - тариф 300+ кВт⋅ч (по умолчанию: 35.00 KZT)
- `LOG_LEVEL` - уровень логирования (по умолчанию: INFO)
- `ALERT_HIGH_LOAD_THRESHOLD` - порог CPU для алертов (по умолчанию: 90%)

### 3. Создание API токена в Proxmox

1. Войдите в Proxmox Web UI
2. Datacenter → Permissions → API Tokens
3. Add → укажите User (например, root@pam)
4. Privilege Separation: отключите (если нужны полные права)
5. Сохраните Token ID и Secret

### 4. Запуск через Docker (рекомендуется)

```bash
docker-compose up -d
```

### 5. Запуск без Docker

```bash
# Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Запустить бота
python -m src.main
```

## 📂 Структура проекта

```
pve-telegram-manager/
├── .github/
│   └── workflows/
│       └── deploy.yml          # CI/CD pipeline
├── src/
│   ├── config.py               # Конфигурация
│   ├── main.py                 # Точка входа
│   ├── database/
│   │   ├── __init__.py
│   │   └── db.py               # База данных
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── common.py           # Общие команды
│   │   ├── vms.py              # Управление VM
│   │   ├── monitoring.py       # Мониторинг
│   │   ├── storage.py          # Хранилище
│   │   ├── finance.py          # Финансы
│   │   ├── logs.py             # Логи
│   │   └── tools.py            # Инструменты
│   ├── keyboards/
│   │   ├── __init__.py
│   │   └── inline.py           # Inline клавиатуры
│   ├── services/
│   │   ├── __init__.py
│   │   ├── proxmox.py          # Proxmox API клиент
│   │   ├── ssh_client.py       # SSH клиент
│   │   └── alerts.py           # Система алертов
│   └── utils/
│       ├── __init__.py
│       ├── formatters.py       # Форматирование
│       └── progress_bars.py    # Прогресс-бары
├── .env.example                # Шаблон переменных
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── README.md
└── requirements.txt
```

## 🎮 Использование

### Команды бота

- `/start` - Запуск бота и главное меню
- `/help` - Справка по командам
- `/vms` - Список всех виртуальных машин
- `/favorites` - Избранные VM
- `/cost <watts> <hours>` - Калькулятор стоимости электричества (например: `/cost 350 720`)

### Главное меню

После команды `/start` появится главное меню с кнопками:

- **🖥️ Virtual Machines** - управление VM/LXC
- **📊 Monitoring** - мониторинг ресурсов
- **💾 Storage** - управление хранилищем
- **🛠️ Tools** - системные инструменты
- **💰 Finance** - калькулятор электричества
- **📝 Logs** - системные логи

## 🔐 Безопасность

- Бот работает только с пользователями из списка `ADMIN_IDS`
- Все команды логируются в базу данных
- Поддержка API токенов вместо пароля
- SSL/TLS соединение с Proxmox

## 🐛 Отладка

Логи бота можно посмотреть:

```bash
# Docker
docker logs pve-telegram-bot -f

# Без Docker
# Логи выводятся в консоль
```

## 🤝 Вклад в проект

Приветствуются Pull Request'ы и Issues!

## 📝 Лицензия

MIT License

## 👨‍💻 Автор

Создано для управления Proxmox VE через Telegram
