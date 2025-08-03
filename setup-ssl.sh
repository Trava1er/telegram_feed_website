#!/bin/bash

# Setup SSL certificates for work-ing.ru
# Run this script on your server

echo "🔒 Setting up SSL certificates for work-ing.ru"

# Step 1: Update DNS settings
echo "📋 First, ensure your DNS A record points to this server:"
echo "   work-ing.ru     A    109.73.205.143"
echo "   www.work-ing.ru A    109.73.205.143"
echo ""
echo "Press Enter when DNS is configured correctly..."
read

# Step 2: Stop current nginx to free port 80
echo "⏹️  Stopping current services..."
docker compose down

# Step 3: Install certbot if not exists
if ! command -v certbot &> /dev/null; then
    echo "📦 Installing certbot..."
    apt update
    apt install -y certbot
fi

# Step 4: Get SSL certificates
echo "🔐 Obtaining SSL certificates..."
certbot certonly --standalone \
    --email your-email@example.com \
    --agree-tos \
    --no-eff-email \
    -d work-ing.ru \
    -d www.work-ing.ru

# Step 5: Copy certificates to docker volumes
echo "📁 Setting up certificate volumes..."
mkdir -p /var/lib/docker/volumes/telegram-feed-website_certbot_certs/_data
cp -r /etc/letsencrypt/* /var/lib/docker/volumes/telegram-feed-website_certbot_certs/_data/

# Step 6: Update docker-compose to use SSL configuration
echo "🔧 Updating docker-compose configuration..."
cp docker-compose.ssl.yml docker-compose.yml

# Step 7: Start services with SSL
echo "🚀 Starting services with SSL..."
docker compose up -d

# Step 8: Setup automatic renewal
echo "⏰ Setting up automatic certificate renewal..."
(crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet && docker compose restart nginx") | crontab -

echo ""
echo "✅ SSL setup complete!"
echo "🌐 Your site should now be available at:"
echo "   https://work-ing.ru"
echo "   https://www.work-ing.ru"
echo ""
echo "🔄 Certificates will auto-renew every 3 AM"
