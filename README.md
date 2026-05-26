# 🤖 Персональний Коуч — Telegram Bot

AI-коуч у Telegram на базі Claude.

## Деплой на Railway

### 1. Завантаж на GitHub
- Створи новий репозиторій на github.com
- Завантаж всі файли з цієї папки

### 2. Задеплой на Railway
- Іди на railway.app → New Project → Deploy from GitHub
- Обери свій репозиторій

### 3. Додай змінні середовища
У Railway → твій проєкт → Variables додай:
```
BOT_TOKEN=твій_токен_від_BotFather
ANTHROPIC_API_KEY=твій_ключ_від_Anthropic
```

### 4. Готово!
Бот запуститься автоматично.

## Команди бота
- /start — почати розмову
- /reset — скинути історію та почати з нуля
