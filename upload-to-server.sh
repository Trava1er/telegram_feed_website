#!/bin/bash

# Скрипт для быстрой загрузки проекта на сервер
# Запускайте с локальной машины

SERVER_IP="109.73.205.143"
SERVER_USER="root"
PROJECT_PATH="/opt/telegram_feed_website"

echo "🚀 Загрузка проекта на сервер $SERVER_IP..."

# Создать архив проекта
echo "📦 Создание архива проекта..."
tar -czf telegram_feed_website.tar.gz \
  --exclude='.git' \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.DS_Store' \
  --exclude='logs' \
  .

# Загрузить на сервер
echo "⬆️  Загрузка на сервер..."
scp telegram_feed_website.tar.gz $SERVER_USER@$SERVER_IP:/tmp/

# Команды для выполнения на сервере
echo "🔧 Настройка на сервере..."
ssh $SERVER_USER@$SERVER_IP << 'EOF'
# Остановить старые контейнеры если есть
cd /opt/telegram_feed_website 2>/dev/null && docker-compose down 2>/dev/null || true

# Создать папку проекта
mkdir -p /opt/telegram_feed_website
cd /opt

# Распаковать новую версию
tar -xzf /tmp/telegram_feed_website.tar.gz -C telegram_feed_website --strip-components=0

# Перейти в папку проекта
cd telegram_feed_website

# Сделать скрипт исполняемым
chmod +x deploy-docker.sh

# Проверить наличие Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Устанавливаю..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Устанавливаю..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

echo "✅ Проект загружен в $PROJECT_PATH"
echo "📋 Содержимое папки:"
ls -la

echo ""
echo "🔒 ВАЖНО: Не забудьте разместить SSL сертификаты!"
echo "mkdir -p ssl"
echo "# Скопируйте ваши сертификаты:"
echo "# ssl/work-ing.ru.crt"
echo "# ssl/work-ing.ru.key"
echo ""
echo "🚀 Для запуска выполните:"
echo "cd /opt/telegram_feed_website"
echo "./deploy-docker.sh"

EOF

# Очистить локальный архив
rm telegram_feed_website.tar.gz

echo ""
echo "✅ Проект успешно загружен на сервер!"
echo "🔗 Подключитесь к серверу: ssh $SERVER_USER@$SERVER_IP"
echo "📁 Перейдите в папку: cd $PROJECT_PATH"
echo "🔒 Разместите SSL сертификаты в папку ssl/"
echo "🚀 Запустите: ./deploy-docker.sh"
