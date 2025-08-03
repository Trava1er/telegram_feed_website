import asyncio
import logging
import re
from typing import Dict, Optional
from datetime import datetime
from telegram import Bot, Update, ChatMember
from telegram.ext import Application, MessageHandler, filters, ContextTypes, ChatMemberHandler
from telegram.error import TelegramError, BadRequest, Forbidden

from core.extensions import db
from models.feed import Feed
from models.post import Post

def extract_contacts_from_text(text):
    """Извлечение контактов из текста сообщения"""
    # Извлечение номеров телефонов
    phone_pattern = r'(?:\+7|8)[\s\-]?\(?[0-9]{3}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}'
    phones = re.findall(phone_pattern, text)
    
    # Извлечение email адресов
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    
    # Извлечение Telegram юзернеймов
    telegram_pattern = r'@[A-Za-z0-9_]{5,}'
    telegrams = re.findall(telegram_pattern, text)
    
    # Извлечение URL
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text)
    
    return {
        'phone_numbers': phones,
        'emails': emails,
        'telegram_users': telegrams,
        'urls': urls
    }


class TelegramBot:
    """Единый сервис для автоматического мониторинга Telegram каналов"""
    
    def __init__(self, app=None):
        self.app = app
        self.bot_token = None
        self.bot = None
        self.application = None
        self.logger = logging.getLogger(__name__)
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Инициализация сервиса с Flask приложением"""
        self.app = app
        
        # Получение токена бота из конфигурации
        self.bot_token = app.config.get('TELEGRAM_BOT_TOKEN')
        
        if not self.bot_token:
            self.logger.warning("TELEGRAM_BOT_TOKEN not found. Bot functionality disabled.")
            return
        
        # Инициализация бота
        self.bot = Bot(token=self.bot_token)
        
        self.logger.info("Telegram bot service initialized")
        
    async def initialize_bot(self):
        """Инициализация бота"""
        if not self.bot_token:
            self.logger.error("Bot token not configured")
            return False
            
        try:
            # Создаем application с увеличенными таймаутами
            from telegram.request import HTTPXRequest
            
            # Увеличиваем таймауты для запросов
            request = HTTPXRequest(
                connection_pool_size=1,
                connect_timeout=30.0,
                read_timeout=30.0,
                write_timeout=30.0,
                pool_timeout=30.0
            )
            
            self.application = Application.builder().token(self.bot_token).request(request).build()
            
            # Универсальный обработчик для всех обновлений (для отладки)
            from telegram.ext import TypeHandler
            debug_handler = TypeHandler(Update, self.debug_all_updates)
            self.application.add_handler(debug_handler, group=-1)
            
            # Обработчик для всех сообщений в каналах
            channel_handler = MessageHandler(
                filters.ChatType.CHANNEL, 
                self.handle_channel_message
            )
            self.application.add_handler(channel_handler)
            
            # Обработчик для изменений статуса участников (когда бот добавляется/удаляется)
            member_handler = ChatMemberHandler(
                self.handle_bot_status_change,
                ChatMemberHandler.MY_CHAT_MEMBER
            )
            self.application.add_handler(member_handler)
            
            # Запуск бота с retry логикой
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await self.application.initialize()
                    await self.application.start()
                    
                    if self.application.updater:
                        await self.application.updater.start_polling(poll_interval=2.0, timeout=30)
                    
                    self.logger.info("✅ Telegram bot initialized and started polling")
                    break
                    
                except Exception as e:
                    self.logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(5)  # Ждем перед повторной попыткой
            
            # Проверяем существующие активные каналы при запуске
            await self.check_existing_channels()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing bot: {str(e)}")
            return False
    
    async def debug_all_updates(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отладочный обработчик для всех обновлений"""
        try:
            if update.channel_post:
                self.logger.info(f"DEBUG: Received channel_post from {update.channel_post.chat.id} ({update.channel_post.chat.title})")
            elif update.edited_channel_post:
                self.logger.info(f"DEBUG: Received edited_channel_post from {update.edited_channel_post.chat.id}")
            elif update.my_chat_member:
                self.logger.info(f"DEBUG: Received my_chat_member update")
            else:
                self.logger.debug(f"DEBUG: Received other update type: {type(update)}")
        except Exception as e:
            self.logger.error(f"Error in debug handler: {e}")
        
    async def stop_bot(self):
        """Остановка бота"""
        try:
            if self.application and self.application.updater:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            self.logger.info("⏸️  Telegram bot stopped")
        except Exception as e:
            self.logger.error(f"Error stopping bot: {str(e)}")

    async def handle_bot_status_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка изменения статуса бота в чате (добавление/удаление)"""
        try:
            self.logger.info(f"Bot status change event received: {update}")
            my_chat_member = update.my_chat_member
            if not my_chat_member:
                self.logger.debug("No my_chat_member data in update")
                return
                
            chat = my_chat_member.chat
            old_status = my_chat_member.old_chat_member.status if my_chat_member.old_chat_member else None
            new_status = my_chat_member.new_chat_member.status if my_chat_member.new_chat_member else None
            
            self.logger.info(f"Status change in {chat.type} {chat.id} ({chat.title}): {old_status} -> {new_status}")
            
            # Проверяем, что это канал
            if chat.type != "channel":
                self.logger.debug(f"Ignoring status change in non-channel: {chat.type}")
                return
                
            channel_id = str(chat.id)
            
            # Бот был добавлен как администратор в канал
            if (old_status in [ChatMember.LEFT, ChatMember.BANNED, None] and 
                new_status == ChatMember.ADMINISTRATOR):
                
                self.logger.info(f"🎉 Bot added as admin to channel: {channel_id} ({chat.title})")
                await self.on_bot_added_to_channel(channel_id, chat)
                
            # Бот был удален из канала
            elif (old_status == ChatMember.ADMINISTRATOR and 
                  new_status in [ChatMember.LEFT, ChatMember.BANNED]):
                
                self.logger.info(f"❌ Bot removed from channel: {channel_id} ({chat.title})")
                await self.on_bot_removed_from_channel(channel_id)
                
        except Exception as e:
            self.logger.error(f"Error handling bot status change: {str(e)}")

    async def on_bot_added_to_channel(self, channel_id: str, chat):
        """Действия при добавлении бота в канал"""
        if not self.app:
            return
            
        with self.app.app_context():
            try:
                # Проверяем, есть ли уже такой фид
                existing_feed = Feed.query.filter_by(telegram_channel_id=channel_id).first()
                
                if not existing_feed:
                    # Создаем новый фид
                    feed = Feed(
                        name=chat.title or chat.username or f"Channel {channel_id}",
                        url=f"https://t.me/{chat.username}" if chat.username else f"https://t.me/c/{abs(int(channel_id))}",
                        telegram_channel_id=channel_id,
                        description=getattr(chat, 'description', '') or f"Auto-detected Telegram channel: {chat.title}",
                        is_active=True
                    )
                    db.session.add(feed)
                    db.session.commit()
                    self.logger.info(f"✅ Created new feed for channel: {chat.title} (ID: {feed.id})")
                else:
                    # Активируем существующий фид
                    existing_feed.is_active = True
                    existing_feed.name = chat.title or existing_feed.name
                    existing_feed.updated_at = datetime.utcnow()
                    db.session.commit()
                    self.logger.info(f"🔄 Reactivated existing feed: {existing_feed.name} (ID: {existing_feed.id})")
                
            except Exception as e:
                db.session.rollback()
                self.logger.error(f"Error processing bot addition to channel {channel_id}: {str(e)}")

    async def on_bot_removed_from_channel(self, channel_id: str):
        """Действия при удалении бота из канала"""
        if not self.app:
            return
            
        with self.app.app_context():
            try:
                # Деактивируем фид
                feed = Feed.query.filter_by(telegram_channel_id=channel_id).first()
                if feed:
                    feed.is_active = False
                    feed.updated_at = datetime.utcnow()
                    db.session.commit()
                    self.logger.info(f"🔇 Deactivated feed: {feed.name} (ID: {feed.id})")
            except Exception as e:
                db.session.rollback()
                self.logger.error(f"Error processing bot removal from channel {channel_id}: {str(e)}")

    async def handle_channel_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нового сообщения в канале"""
        try:
            message = update.channel_post or update.edited_channel_post
            if not message:
                self.logger.debug("No channel message found in update")
                return
                
            chat = message.chat
            channel_id = str(chat.id)
            self.logger.info(f"📨 Received message from channel {channel_id} ({chat.title}): {message.text or 'media message'}")
            
            # Проверяем, есть ли этот канал в нашей БД
            if not self.app:
                return
                
            with self.app.app_context():
                feed = Feed.query.filter_by(telegram_channel_id=channel_id, is_active=True).first()
                if not feed:
                    # Автоматически создаем фид для нового канала
                    feed = Feed(
                        name=chat.title or chat.username or f"Channel {channel_id}",
                        url=f"https://t.me/{chat.username}" if chat.username else f"https://t.me/c/{abs(int(channel_id))}",
                        telegram_channel_id=channel_id,
                        description=f"Auto-detected channel: {chat.title}",
                        is_active=True
                    )
                    db.session.add(feed)
                    db.session.commit()
                    self.logger.info(f"📁 Auto-created feed for new channel: {chat.title} (ID: {feed.id})")
                
                # Создаем пост из сообщения
                post_data = await self.parse_telegram_message(message, feed.id)
                if post_data:
                    # Проверяем, не существует ли уже такое сообщение
                    existing_post = Post.get_by_telegram_message_id(
                        post_data["telegram_message_id"], 
                        feed.id
                    )
                    
                    if existing_post:
                        if update.edited_channel_post:
                            # Обновляем существующее сообщение
                            existing_post.content = post_data["content"]
                            existing_post.is_edited = True
                            existing_post.updated_at = datetime.utcnow()
                            if post_data["contacts"]:
                                existing_post.set_contacts(post_data["contacts"])
                            db.session.commit()
                            self.logger.info(f"✏️  Updated post {existing_post.id} in feed {feed.name}")
                    else:
                        # Создаем новое сообщение
                        new_post = Post(
                            telegram_message_id=post_data["telegram_message_id"],
                            content=post_data["content"],
                            feed_id=feed.id,
                            telegram_date=post_data["telegram_date"],
                            media_url=post_data["media_url"],
                            media_type=post_data["media_type"],
                            is_edited=post_data["is_edited"],
                            views=post_data.get("views", 0)
                        )
                        
                        # Установка контактов
                        if post_data["contacts"]:
                            new_post.set_contacts(post_data["contacts"])
                        
                        db.session.add(new_post)
                        db.session.commit()
                        
                        # Обновляем время последней синхронизации фида
                        feed.update_last_sync()
                        
                        self.logger.info(f"💾 Saved new post {new_post.id} from {feed.name}: {post_data['content'][:50]}...")
                        
        except Exception as e:
            if self.app:
                with self.app.app_context():
                    db.session.rollback()
            self.logger.error(f"Error handling channel message: {str(e)}")
    
    async def parse_telegram_message(self, message, feed_id: int) -> Optional[Dict]:
        """Парсит сообщение Telegram в формат для БД"""
        try:
            content = message.text or message.caption or ""
            
            # Проверяем, что сообщение не пустое (есть текст или медиа)
            has_content = bool(content.strip())
            has_media = bool(message.photo or message.video or message.document or 
                           message.animation or message.voice or message.audio)
            
            # Дополнительная проверка: если есть только текст, он должен содержать значимые символы
            if has_content and not has_media:
                # Проверяем, что текст содержит не только пробелы, переводы строк и специальные символы
                meaningful_content = ''.join(c for c in content if c.isalnum() or c in '.,!?;:-()[]{}@#$%^&*+=<>/\\|`~"\'').strip()
                if not meaningful_content:
                    self.logger.info(f"Skipping message {message.message_id} with only whitespace/special chars")
                    return None
            
            if not has_content and not has_media:
                self.logger.info(f"Skipping empty message {message.message_id} from feed {feed_id}")
                return None
            
            # Обработка медиафайлов
            media_url = None
            media_type = None
            
            if message.photo:
                # Берем самое большое фото
                photo = message.photo[-1]
                try:
                    file = await self.bot.get_file(photo.file_id)
                    media_url = file.file_path  # Сохраняем только file_path
                    media_type = "photo"
                except Exception as e:
                    self.logger.error(f"Error getting photo file path: {e}")
                    media_url = None
                    media_type = None
            elif message.video:
                try:
                    file = await self.bot.get_file(message.video.file_id)
                    media_url = file.file_path  # Сохраняем только file_path
                    media_type = "video"
                except Exception as e:
                    self.logger.error(f"Error getting video file path: {e}")
            elif message.document:
                try:
                    file = await self.bot.get_file(message.document.file_id)
                    media_url = file.file_path  # Сохраняем только file_path
                    media_type = "document"
                except Exception as e:
                    self.logger.error(f"Error getting document file path: {e}")
            elif message.animation:
                try:
                    file = await self.bot.get_file(message.animation.file_id)
                    media_url = file.file_path  # Сохраняем только file_path
                except Exception as e:
                    self.logger.error(f"Error getting animation file path: {e}")
                media_type = "animation"
            elif message.voice:
                try:
                    file = await self.bot.get_file(message.voice.file_id)
                    media_url = file.file_path  # Сохраняем только file_path
                except Exception as e:
                    self.logger.error(f"Error getting voice file path: {e}")
                media_type = "voice"
            elif message.audio:
                try:
                    file = await self.bot.get_file(message.audio.file_id)
                    media_url = file.file_path  # Сохраняем только file_path
                except Exception as e:
                    self.logger.error(f"Error getting audio file path: {e}")
                media_type = "audio"
            
            # Извлечение контактов из текста
            contacts = extract_contacts_from_text(content) if content else None
            
            return {
                "telegram_message_id": message.message_id,
                "content": content,
                "media_url": media_url,
                "media_type": media_type,
                "feed_id": feed_id,
                "telegram_date": message.date,
                "is_edited": hasattr(message, 'edit_date') and message.edit_date is not None,
                "views": getattr(message, 'views', 0) or 0,
                "contacts": contacts
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing telegram message: {str(e)}")
            return None

    async def check_existing_channels(self):
        """Проверяет существующие активные каналы при запуске бота"""
        if not self.app:
            return
            
        try:
            # Ждем, пока бот полностью инициализируется
            await asyncio.sleep(2)
            
            with self.app.app_context():
                # Получаем все активные фиды с telegram_channel_id
                active_feeds = Feed.query.filter_by(is_active=True).filter(
                    Feed.telegram_channel_id != None
                ).all()
                
                self.logger.info(f"🔍 Checking {len(active_feeds)} existing channels...")
                
                for feed in active_feeds:
                    try:
                        # Проверяем, что бот все еще админ в канале
                        if self.application and self.application.bot:
                            chat_member = await self.application.bot.get_chat_member(
                                feed.telegram_channel_id, 
                                self.application.bot.id
                            )
                            if chat_member.status == ChatMember.ADMINISTRATOR:
                                self.logger.info(f"✅ Monitoring channel: {feed.name} ({feed.telegram_channel_id})")
                            else:
                                # Деактивируем фид, если бот больше не админ
                                feed.is_active = False
                                feed.updated_at = datetime.utcnow()
                                db.session.commit()
                                self.logger.info(f"🔇 Deactivated {feed.name} - bot is no longer admin")
                        else:
                            self.logger.warning("Bot application not initialized, skipping channel check")
                            
                    except Exception as e:
                        self.logger.warning(f"Could not check status for channel {feed.name}: {str(e)}")
                        # Не деактивируем фид при ошибке, может быть временная проблема
                        
                    await asyncio.sleep(0.1)  # Пауза между проверками
                    
        except Exception as e:
            self.logger.error(f"Error during startup channel check: {str(e)}")

    async def get_channel_info(self, channel_id: str) -> Optional[Dict]:
        """Получает информацию о канале"""
        try:
            if not self.bot:
                self.logger.error("Bot not initialized")
                return None
                
            chat = await self.bot.get_chat(channel_id)
            return {
                "id": str(chat.id),
                "title": chat.title,
                "username": chat.username,
                "description": getattr(chat, 'description', ''),
                "type": chat.type
            }
        except Exception as e:
            self.logger.error(f"Error getting channel info for {channel_id}: {str(e)}")
            return None

    async def sync_channel_history(self, channel_id: str, feed_id: int, limit: int = 20):
        """Синхронизация истории сообщений канала - недоступно для bot token"""
        self.logger.warning("History sync not available for bot tokens - only real-time monitoring")
        return 0
    
    # === СОВМЕСТИМОСТЬ С CLI ===
    
    async def start_client(self):
        """Совместимость с CLI - запуск клиента"""
        return await self.initialize_bot()
    
    async def stop_client(self):
        """Совместимость с CLI - остановка клиента"""
        await self.stop_bot()
    
    async def sync_all_feeds(self, limit_per_feed: int = 50) -> Dict[int, int]:
        """Совместимость с CLI - синхронизация недоступна для ботов"""
        self.logger.warning("History sync not available for bot tokens - only real-time monitoring")
        return {}
    
    async def sync_channel_to_database(self, feed_id: int, limit: int = 50) -> int:
        """Совместимость с CLI - синхронизация недоступна для ботов"""
        self.logger.warning("History sync not available for bot tokens - only real-time monitoring")
        return 0
    
    async def start_monitoring(self):
        """Запуск мониторинга в реальном времени"""
        if not await self.initialize_bot():
            return False
            
        try:
            self.logger.info("🚀 Starting Telegram channel monitoring...")
            self.logger.info("📡 Bot will automatically detect channels where it's admin")
            self.logger.info("💾 New messages will be saved to database automatically")
            self.logger.info("📨 Monitoring started. Press Ctrl+C to stop.")
            
            # Поддержание работы - простой цикл
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                self.logger.info("⏸️  Monitoring stopped by user")
                await self.stop_bot()
                
        except Exception as e:
            self.logger.error(f"Error during monitoring: {str(e)}")
            return False


# Глобальный экземпляр
telegram_bot = TelegramBot()


# === ФУНКЦИИ ДЛЯ ЗАПУСКА ===

async def start_realtime_monitoring():
    """Запуск мониторинга в реальном времени"""
    if not telegram_bot.bot:
        logging.error("Telegram bot not initialized")
        return
    
    await telegram_bot.start_monitoring()


if __name__ == "__main__":
    # Для тестирования
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from app import create_app
    
    app = create_app()
    telegram_bot.init_app(app)
    
    asyncio.run(start_realtime_monitoring())
