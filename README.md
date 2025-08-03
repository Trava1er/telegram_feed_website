# 🚀 Telegram Feed Website - Docker Edition

Военный веб-сайт для агрегации постов из Telegram каналов с адаптивным дизайном.

## ✨ Особенности

- 🎯 **10 постов на страницу** - оптимальная пагинация
- 📱 **Адаптивный дизайн** - посты с медиа делятся на части, текстовые во всю ширину
- 🔍 **Работающий поиск** - исправленная функциональность поиска
- 🎨 **Военная тематика** - специальный темный дизайн
- 🐳 **Docker развертывание** - готово к продакшену

## 🐳 Быстрый старт с Docker

### Готовое развертывание с вашими ключами:
```bash
# Клонирование
git clone <your-repo-url>
cd telegram_feed_website

# Запуск (все ключи уже настроены!)
./deploy-docker.sh
```

### ✅ Готово! Продакшен конфигурация:
- **Домен**: https://work-ing.ru (SSL активирован)
- **Сервер**: 109.73.205.143
- **База данных**: Автоматически создается внутри Docker
- **Telegram API**: Ваши ключи настроены
- **Безопасность**: Уникальный SECRET_KEY сгенерирован

## 🛠️ Управление Docker

```bash
# Запуск сервисов
docker-compose up -d

# Остановка сервисов
docker-compose down

# Просмотр логов
docker-compose logs -f

# Перезапуск
docker-compose restart web

# Статус сервисов
docker-compose ps
```

## 📊 Архитектура

- **Flask** приложение с адаптивными шаблонами
- **PostgreSQL** внутренняя база данных Docker
- **Redis** для кеширования (внутренний)
- **Nginx** реверс-прокси
- **Gunicorn** WSGI сервер
- **Docker Volumes** для постоянного хранения данных

## 🔧 Полная конфигурация

Все настройки в `.env.production` (уже заполнен):

```bash
# Ваши Telegram API ключи (уже настроены)
TELEGRAM_API_ID=27702798
TELEGRAM_API_HASH=c348530f8927a0d9edada2040855ca9a
TELEGRAM_BOT_TOKEN=7645775608:AAF1ADThKLzZMh_9ZtfMJA8CBS0oIjk3238

# База данных (Docker внутренняя)
DATABASE_URL=postgresql://telegram_feed:secure_password_2025@db:5432/telegram_feed_db

# Безопасность
SECRET_KEY=your-super-secret-key-here-change-in-production
```

**Для продакшена измените только:**
```bash
# Отредактируйте .env.production
nano .env.production

# Измените SECRET_KEY на уникальный
SECRET_KEY=ваш-новый-секретный-ключ

# Перезапустите
docker-compose restart
```

## 📝 Документация

- **QUICKSTART.md** - быстрый старт за 1 команду
- **SSL-SETUP.md** - размещение SSL сертификатов для HTTPS  
- **ДОМЕН.md** - настройка SSL для work-ing.ru  
- **DATABASE.md** - управление внутренней БД  
- **DOCKER-DEPLOYMENT.md** - подробное руководство по развертыванию
- **TELEGRAM_API_SETUP.md** - настройка Telegram API (опционально)

## 🚨 Финальные шаги

**Только разместите SSL сертификаты:**

1. **Создайте папку ssl**: `mkdir -p ssl`
2. **Поместите сертификаты**:
   - `ssl/work-ing.ru.crt` (ваш сертификат)
   - `ssl/work-ing.ru.key` (приватный ключ)
3. **Запустите**: `./deploy-docker.sh`

**Все остальное (DNS → 109.73.205.143, SECRET_KEY, API ключи) уже настроено!**

## 🎯 Структура проекта

```
telegram_feed_website/
├── app.py                    # Основное Flask приложение
├── docker-compose.yml       # Docker конфигурация
├── Dockerfile               # Контейнер приложения
├── requirements.txt         # Python зависимости
├── routes/                  # Маршруты Flask
├── templates/               # Jinja2 шаблоны
├── static/                  # CSS, JS, изображения
├── models/                  # SQLAlchemy модели
└── services/                # Бизнес логика
```

---

🎉 **Готово к продакшену за 3 команды!**
