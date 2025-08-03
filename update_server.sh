#!/bin/bash

# Update server with full project code
echo "Updating server with full project code..."

# Stop containers
docker compose down

# Backup current code
mv telegram-feed-app telegram-feed-app-backup-$(date +%Y%m%d_%H%M%S)

# Extract new code
tar -xzf telegram_feed_website_full.tar.gz
mv telegram_feed_website telegram-feed-app

# Set correct permissions
chown -R root:root telegram-feed-app
chmod +x telegram-feed-app/*.sh

# Start containers
cd telegram-feed-app
docker compose up -d --build

# Check status
docker compose ps
docker compose logs web --tail=10

echo "Update complete!"
