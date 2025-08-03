# 🔒 SSL Setup for work-ing.ru

## Быстрая настройка HTTPS

### 1. Проверьте DNS
Убедитесь, что ваш домен указывает на правильный IP:
```
work-ing.ru     A    109.73.205.143
www.work-ing.ru A    109.73.205.143
```

### 2. Запустите автоматическую настройку
На сервере выполните:
```bash
cd /root/telegram-feed-website
git pull origin main
./setup-ssl.sh
```

### 3. Альтернативный способ (ручной)

#### Получить сертификаты:
```bash
# Остановить nginx
docker compose down

# Получить сертификаты
certbot certonly --standalone \
    --email your-email@example.com \
    --agree-tos \
    --no-eff-email \
    -d work-ing.ru \
    -d www.work-ing.ru

# Использовать SSL конфигурацию
cp docker-compose.ssl.yml docker-compose.yml
cp nginx-ssl.conf nginx-docker.conf

# Запустить с SSL
docker compose up -d
```

### 4. Автообновление сертификатов
```bash
# Добавить в crontab
echo "0 3 * * * certbot renew --quiet && docker compose restart nginx" | crontab -
```

### 5. Проверка
После настройки сайт будет доступен по HTTPS:
- https://work-ing.ru
- https://www.work-ing.ru

HTTP будет автоматически редиректить на HTTPS.
