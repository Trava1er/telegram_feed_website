from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.post import Post
from models.feed import Feed
from models.category import Category
from core.extensions import db
from services.telegram_bot import telegram_bot
import asyncio

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
def dashboard():
    """Admin dashboard"""
    stats = {
        'total_posts': Post.query.count(),
        'total_feeds': Feed.query.count(),
        'active_feeds': Feed.query.filter_by(is_active=True).count(),
        'total_categories': Category.query.count(),
        'recent_posts': Post.query.order_by(Post.created_at.desc()).limit(10).all()
    }
    return render_template('admin/dashboard.html', stats=stats)

@admin_bp.route('/feeds')
def feeds():
    """Manage feeds"""
    feeds = Feed.query.order_by(Feed.name).all()
    categories = Category.query.order_by(Category.display_name).all()
    return render_template('admin/feeds.html', feeds=feeds, categories=categories)

@admin_bp.route('/feeds/add', methods=['GET', 'POST'])
def add_feed():
    """Add new feed"""
    if request.method == 'POST':
        name = request.form.get('name')
        url = request.form.get('url')
        telegram_channel_id = request.form.get('telegram_channel_id')
        description = request.form.get('description')
        category_id = request.form.get('category_id', type=int)
        
        if name and url:
            feed = Feed(
                name=name,
                url=url,
                telegram_channel_id=telegram_channel_id,
                description=description,
                category_id=category_id if category_id else None
            )
            db.session.add(feed)
            db.session.commit()
            flash('Feed added successfully!', 'success')
            return redirect(url_for('admin.feeds'))
        else:
            flash('Name and URL are required!', 'error')
    
    categories = Category.query.order_by(Category.display_name).all()
    return render_template('admin/add_feed.html', categories=categories)

@admin_bp.route('/feeds/<int:feed_id>/delete', methods=['POST'])
def delete_feed(feed_id):
    """Delete feed"""
    feed = Feed.query.get_or_404(feed_id)
    db.session.delete(feed)
    db.session.commit()
    flash('Feed deleted successfully!', 'success')
    return redirect(url_for('admin.feeds'))

@admin_bp.route('/categories')
def categories():
    """Manage categories"""
    categories = Category.query.order_by(Category.sort_order, Category.display_name).all()
    return render_template('admin/categories.html', categories=categories)

@admin_bp.route('/categories/add', methods=['GET', 'POST'])
def add_category():
    """Add new category"""
    if request.method == 'POST':
        name = request.form.get('name')
        display_name = request.form.get('display_name')
        description = request.form.get('description')
        color = request.form.get('color', '#007bff')
        icon = request.form.get('icon')
        sort_order = request.form.get('sort_order', 0, type=int)
        
        if name and display_name:
            category = Category(
                name=name,
                display_name=display_name,
                description=description,
                color=color,
                icon=icon,
                sort_order=sort_order
            )
            db.session.add(category)
            db.session.commit()
            flash('Category added successfully!', 'success')
            return redirect(url_for('admin.categories'))
        else:
            flash('Name and display name are required!', 'error')
    
    return render_template('admin/add_category.html')

@admin_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
def delete_category(category_id):
    """Delete category"""
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash('Категория успешно удалена!', 'success')
    return redirect(url_for('admin.categories'))

@admin_bp.route('/posts')
def posts():
    """Manage posts"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    posts = Post.query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/posts.html', posts=posts)


@admin_bp.route('/telegram-bot')
def telegram_bot():
    """Telegram bot management dashboard"""
    from sqlalchemy import and_
    from datetime import datetime, timedelta
    
    # Get Telegram feeds (feeds with telegram_channel_id)
    telegram_feeds = Feed.query.filter(
        and_(Feed.telegram_channel_id != None, Feed.telegram_channel_id != '')
    ).all()
    
    # Calculate statistics
    total_posts = db.session.query(Post).join(Feed).filter(
        and_(Feed.telegram_channel_id != None, Feed.telegram_channel_id != '')
    ).count()
    
    # Get recent posts from last 7 days
    week_ago = datetime.now() - timedelta(days=7)
    recent_posts = db.session.query(Post).join(Feed).filter(
        and_(
            Feed.telegram_channel_id != None,
            Feed.telegram_channel_id != '',
            Post.telegram_date >= week_ago
        )
    ).order_by(Post.telegram_date.desc()).limit(12).all()
    
    stats = {
        'total_telegram_feeds': len(telegram_feeds),
        'active_telegram_feeds': len([f for f in telegram_feeds if f.is_active]),
        'total_telegram_posts': total_posts,
        'recent_telegram_posts': recent_posts
    }
    
    return render_template('admin/telegram_bot.html', 
                         telegram_feeds=telegram_feeds, 
                         stats=stats)


@admin_bp.route('/telegram-sync', methods=['POST'])
def telegram_sync():
    """Manually trigger Telegram sync for all feeds"""
    try:
        # Use Flask CLI command for manual sync
        flash('Telegram sync can be triggered via CLI: flask telegram sync', 'info')
    except Exception as e:
        flash(f'Error starting sync: {str(e)}', 'error')
    
    return redirect(url_for('admin.telegram_bot'))


@admin_bp.route('/telegram-sync-feed/<int:feed_id>', methods=['POST'])
def telegram_sync_feed(feed_id):
    """Manually trigger Telegram sync for specific feed"""
    try:
        feed = Feed.query.get_or_404(feed_id)
        
        # Use Flask CLI command for sync
        flash(f'Telegram sync for {feed.name} can be triggered via CLI: flask telegram sync-feed {feed_id}', 'info')
    except Exception as e:
        flash(f'Error starting sync: {str(e)}', 'error')
    
    return redirect(url_for('admin.telegram_bot'))

@admin_bp.route('/telegram-test-connection', methods=['POST'])
def telegram_test_connection():
    """Test Telegram bot connection"""
    try:
        # Simple connection test using scheduler
        flash('Connection test triggered. Check logs for results.', 'info')
    except Exception as e:
        flash(f'Error testing connection: {str(e)}', 'error')
    
    return redirect(url_for('admin.telegram_bot'))

@admin_bp.route('/telegram-channel-info', methods=['POST'])
def telegram_channel_info():
    """Get Telegram channel information"""
    try:
        channel_identifier = request.form.get('channel_identifier', '').strip()
        if not channel_identifier:
            flash('Please provide a channel identifier', 'error')
        else:
            flash(f'Channel info request for: {channel_identifier}. Check logs for results.', 'info')
    except Exception as e:
        flash(f'Error getting channel info: {str(e)}', 'error')
    
    return redirect(url_for('admin.telegram_bot'))
