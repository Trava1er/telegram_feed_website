"""
Management commands for Telegram bot operations.
"""

import asyncio
import click
from flask.cli import with_appcontext

from services.telegram_bot import telegram_bot, start_realtime_monitoring
from models.feed import Feed
from core.extensions import db


@click.group()
def telegram():
    """Telegram bot management commands."""
    pass


@telegram.command()
@with_appcontext
@click.option('--limit', default=50, help='Number of messages to fetch per channel')
def sync(limit):
    """Sync all Telegram feeds (History sync not available for bot tokens)."""
    click.echo(f"⚠️  History sync not available for bot tokens.")
    click.echo(f"Bot tokens can only monitor NEW messages in real-time.")
    click.echo(f"Use 'flask telegram monitor' to start real-time monitoring.")
    
    # Show current feeds
    feeds = Feed.query.filter_by(is_active=True).filter(Feed.telegram_channel_id != None).all()
    if feeds:
        click.echo(f"\nActive Telegram feeds ({len(feeds)}):")
        for feed in feeds:
            click.echo(f"  - {feed.name} ({feed.telegram_channel_id})")
    else:
        click.echo("\nNo active Telegram feeds found.")


@telegram.command()
@with_appcontext
@click.argument('feed_id', type=int)
@click.option('--limit', default=50, help='Number of messages to fetch')
def sync_feed(feed_id, limit):
    """Sync a specific Telegram feed by ID (History sync not available for bot tokens)."""
    feed = Feed.query.get(feed_id)
    if not feed:
        click.echo(f"Feed with ID {feed_id} not found.")
        return
    
    if not feed.telegram_channel_id:
        click.echo(f"Feed '{feed.name}' has no Telegram channel ID.")
        return
    
    click.echo(f"⚠️  History sync not available for bot tokens.")
    click.echo(f"Feed '{feed.name}' can only be monitored in real-time.")
    click.echo(f"Use 'flask telegram monitor' to start monitoring.")


@telegram.command()
@with_appcontext
@click.argument('channel_identifier')
def channel_info(channel_identifier):
    """Get information about a Telegram channel."""
    click.echo(f"Getting info for channel: {channel_identifier}")
    
    async def get_info():
        await telegram_bot.start_client()
        try:
            info = await telegram_bot.get_channel_info(channel_identifier)
            if info:
                click.echo("Channel Information:")
                click.echo(f"  ID: {info['id']}")
                click.echo(f"  Title: {info['title']}")
                click.echo(f"  Username: @{info['username']}" if info['username'] else "  Username: None")
                click.echo(f"  Description: {info['description'] or 'None'}")
                click.echo(f"  Members: {info['members_count'] or 'Unknown'}")
                click.echo(f"  Type: {info['type'] or 'Unknown'}")
            else:
                click.echo("Channel not found or is private.")
        finally:
            await telegram_bot.stop_client()
    
    asyncio.run(get_info())


@telegram.command()
@with_appcontext
@click.argument('channel_identifier')
@click.argument('name')
@click.option('--description', help='Feed description')
def add_feed(channel_identifier, name, description):
    """Add a new Telegram feed."""
    click.echo(f"Adding new feed for channel: {channel_identifier}")
    
    async def add_new_feed():
        await telegram_bot.start_client()
        try:
            # Get channel info first
            info = await telegram_bot.get_channel_info(channel_identifier)
            if not info:
                click.echo("Channel not found or is private.")
                return
            
            # Check if feed already exists
            existing_feed = Feed.query.filter_by(telegram_channel_id=channel_identifier).first()
            if existing_feed:
                click.echo(f"Feed for this channel already exists: {existing_feed.name}")
                return
            
            # Create new feed
            feed = Feed(
                name=name,
                url=f"https://t.me/{info['username']}" if info['username'] else f"https://t.me/c/{abs(info['id'])}",
                telegram_channel_id=channel_identifier,
                description=description or info['description'] or f"Telegram channel: {info['title']}",
                is_active=True
            )
            
            db.session.add(feed)
            db.session.commit()
            
            click.echo(f"Feed '{name}' added successfully (ID: {feed.id})")
            click.echo(f"Channel: {info['title']} (@{info['username']})")
            
        except Exception as e:
            db.session.rollback()
            click.echo(f"Error adding feed: {e}")
        finally:
            await telegram_bot.stop_client()
    
    asyncio.run(add_new_feed())


@telegram.command('monitor')
@with_appcontext
def monitor():
    """Start real-time monitoring of new messages."""
    click.echo("🚀 Starting real-time Telegram monitoring...")
    click.echo("📡 This will monitor only NEW messages from subscribed channels.")
    click.echo("⏹️  Press Ctrl+C to stop.")
    
    def run_monitor():
        asyncio.run(start_realtime_monitoring())
    
    try:
        run_monitor()
    except KeyboardInterrupt:
        click.echo("\n⏸️  Monitoring stopped by user.")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)


@telegram.command()
@with_appcontext
def list_feeds():
    """List all Telegram feeds."""
    feeds = Feed.query.filter(Feed.telegram_channel_id != None).all()
    
    if not feeds:
        click.echo("No Telegram feeds found.")
        return
    
    click.echo("Telegram Feeds:")
    for feed in feeds:
        status = "Active" if feed.is_active else "Inactive"
        click.echo(f"  ID: {feed.id}")
        click.echo(f"  Name: {feed.name}")
        click.echo(f"  Channel: {feed.telegram_channel_id}")
        click.echo(f"  Status: {status}")
        click.echo(f"  URL: {feed.url}")
        click.echo("  ---")


@telegram.command()
@with_appcontext
def test_connection():
    """Test Telegram API connection."""
    click.echo("Testing Telegram API connection...")
    
    async def test():
        success = await telegram_bot.start_client()
        if success:
            click.echo("✅ Successfully connected to Telegram API")
            
            # Получаем информацию о боте
            try:
                if telegram_bot.bot:
                    me = await telegram_bot.bot.get_me()
                    click.echo(f"Bot info: {me.first_name} (@{me.username})")
                else:
                    click.echo("Bot object not available")
            except Exception as e:
                click.echo(f"Could not get bot info: {e}")
                
        else:
            click.echo("❌ Failed to connect to Telegram API")
        
        await telegram_bot.stop_client()
    
    asyncio.run(test())


def init_app(app):
    """Initialize CLI commands with Flask app."""
    app.cli.add_command(telegram)
